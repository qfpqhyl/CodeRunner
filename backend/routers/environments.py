"""Environment management routes."""
import subprocess
import os
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_

from models.database import get_db, User, UserEnvironment
from models.models import (
    UserEnvironmentCreate, UserEnvironmentUpdate, UserEnvironmentResponse,
    EnvironmentInfo, PackageInfo, PackageInstallRequest, PackageInstallResponse
)
from services.auth import get_current_user, get_current_admin_user
from utils.utils import log_system_event, get_client_info

router = APIRouter(tags=["environments"])


@router.get("/conda-environments")
def get_conda_environments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get available conda environments based on user permissions"""
    try:
        # Get user's accessible environments from models.database
        accessible_envs = set()

        # Always include base environment
        accessible_envs.add("base")

        # Add user's own environments
        user_envs = db.query(UserEnvironment).filter(
            UserEnvironment.user_id == current_user.id,
            UserEnvironment.is_active == True
        ).all()
        for env in user_envs:
            accessible_envs.add(env.env_name)

        # Add public environments (for non-admin users)
        if not current_user.is_admin:
            public_envs = db.query(UserEnvironment).filter(
                UserEnvironment.is_public == True,
                UserEnvironment.is_active == True,
                UserEnvironment.user_id != current_user.id
            ).all()
            for env in public_envs:
                accessible_envs.add(env.env_name)

        # If admin, add all active environments except runner
        if current_user.is_admin:
            all_envs = db.query(UserEnvironment).filter(
                UserEnvironment.is_active == True
            ).all()
            for env in all_envs:
                if env.env_name != "runner":  # Admin can't see runner environment
                    accessible_envs.add(env.env_name)

        # Get actual conda environments to verify which ones exist
        result = subprocess.run(
            ["conda", "env", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            # Parse conda env list output
            conda_envs = set()
            lines = result.stdout.split('\n')

            for line in lines:
                line = line.strip()
                # Skip empty lines, headers, and lines with #
                if not line or line.startswith('#') or line.startswith('Name'):
                    continue

                # Extract environment name (first column)
                parts = line.split()
                if parts:
                    env_name = parts[0]
                    conda_envs.add(env_name)

            # Only return environments that exist in conda and user has access to
            final_envs = list(accessible_envs.intersection(conda_envs))

            # Ensure base is always included even if not in conda list
            if "base" not in final_envs:
                final_envs.insert(0, "base")

            return final_envs
        else:
            # Fallback: return base + user environments from models.database
            return list(accessible_envs)

    except subprocess.TimeoutExpired:
        # Return base + user environments from models.database on timeout
        return ["base"]
    except Exception as e:
        # Log error but return basic environments
        print(f"Failed to get conda environments: {e}")
        return ["base"]


@router.post("/user-environments", response_model=UserEnvironmentResponse)
def create_user_environment(
    env_data: UserEnvironmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Create a new user environment"""
    # Check if user has reached their environment limit (non-admin users can only have 1)
    if not current_user.is_admin:
        current_count = db.query(UserEnvironment).filter(UserEnvironment.user_id == current_user.id).count()
        if current_count >= 1:
            raise HTTPException(
                status_code=429,
                detail="普通用户只能创建一个环境"
            )

    # Check if environment name already exists
    existing_env = db.query(UserEnvironment).filter(UserEnvironment.env_name == env_data.env_name).first()
    if existing_env:
        raise HTTPException(status_code=400, detail="环境名称已存在")

    # Validate environment name format
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', env_data.env_name):
        raise HTTPException(status_code=400, detail="环境名称只能包含字母、数字、下划线和连字符")

    try:
        # Create conda environment
        create_cmd = f"conda create -n {env_data.env_name} python={env_data.python_version} -y"
        result = subprocess.run(
            create_cmd.split(),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "环境创建失败"
            raise HTTPException(status_code=500, detail=f"Conda环境创建失败: {error_msg}")

        # Install additional packages if specified
        if env_data.packages:
            pip_cmd = f"conda run -n {env_data.env_name} pip"
            for package in env_data.packages:
                install_cmd = f"{pip_cmd} install {package}".split()
                install_result = subprocess.run(
                    install_cmd,
                    capture_output=True,
                    text=True,
                    timeout=120  # 2 minutes per package
                )
                if install_result.returncode != 0:
                    # Log warning but continue with environment creation
                    print(f"Failed to install package {package}: {install_result.stderr}")

        # Generate conda environment YAML
        conda_yaml = f"""name: {env_data.env_name}
channels:
  - defaults
dependencies:
  - python={env_data.python_version}
"""
        if env_data.packages:
            for package in env_data.packages:
                conda_yaml += f"  - {package}\n"

        # Create database record
        user_env = UserEnvironment(
            user_id=current_user.id,
            env_name=env_data.env_name,
            display_name=env_data.display_name,
            description=env_data.description,
            python_version=env_data.python_version,
            conda_yaml=conda_yaml,
            is_public=env_data.is_public
        )

        db.add(user_env)
        db.commit()
        db.refresh(user_env)

        # Log environment creation
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="environment_create",
            resource_type="user_environment",
            resource_id=user_env.id,
            details={
                "env_name": env_data.env_name,
                "display_name": env_data.display_name,
                "python_version": env_data.python_version,
                "packages": env_data.packages,
                "is_public": env_data.is_public
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        # Add owner name to response
        user_env.owner_name = current_user.username
        return user_env

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="环境创建超时")
    except HTTPException:
        raise
    except Exception as e:
        # Log failed environment creation
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="environment_create",
            resource_type="user_environment",
            details={
                "env_name": env_data.env_name,
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"环境创建失败: {str(e)}")


@router.get("/user-environments", response_model=list[UserEnvironmentResponse])
def get_user_environments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get environments available to the current user"""
    environments = []

    # Always include base environment
    environments.append({
        "id": 0,
        "user_id": 0,
        "env_name": "base",
        "display_name": "基础环境",
        "description": "系统默认的conda基础环境",
        "python_version": "3.11",
        "is_active": True,
        "is_public": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_used": None,
        "owner_name": "system"
    })

    # Get user's own environments
    user_envs = db.query(UserEnvironment).filter(UserEnvironment.user_id == current_user.id).all()
    for env in user_envs:
        env.owner_name = current_user.username
        environments.append(env)

    # Get public environments from other users (excluding admin-only)
    if not current_user.is_admin:
        public_envs = db.query(UserEnvironment).filter(
            UserEnvironment.is_public == True,
            UserEnvironment.user_id != current_user.id
        ).all()
        for env in public_envs:
            owner = db.query(User).filter(User.id == env.user_id).first()
            env.owner_name = owner.username if owner else "unknown"
            environments.append(env)

    return environments


@router.get("/user-environments/{env_id}", response_model=UserEnvironmentResponse)
def get_user_environment(
    env_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific user environment"""
    # Handle base environment (id = 0)
    if env_id == 0:
        return {
            "id": 0,
            "user_id": 0,
            "env_name": "base",
            "display_name": "基础环境",
            "description": "系统默认的conda基础环境",
            "python_version": "3.11",
            "is_active": True,
            "is_public": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "last_used": None,
            "owner_name": "system"
        }

    # Get user environment
    env = db.query(UserEnvironment).filter(UserEnvironment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="环境未找到")

    # Check permissions
    if env.user_id != current_user.id and not env.is_public and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权访问此环境")

    # Add owner name
    owner = db.query(User).filter(User.id == env.user_id).first()
    env.owner_name = owner.username if owner else "unknown"

    return env


@router.put("/user-environments/{env_id}", response_model=UserEnvironmentResponse)
def update_user_environment(
    env_id: int,
    env_update: UserEnvironmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Update a user environment"""
    # Cannot update base environment
    if env_id == 0:
        raise HTTPException(status_code=400, detail="不能修改基础环境")

    env = db.query(UserEnvironment).filter(UserEnvironment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="环境未找到")

    # Check permissions - only owner or admin can update
    if env.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权修改此环境")

    # Update fields
    update_data = env_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(env, field, value)

    env.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(env)

    # Log environment update
    log_system_event(
        db=db,
        user_id=current_user.id,
        action="environment_update",
        resource_type="user_environment",
        resource_id=env.id,
        details=update_data,
        ip_address=client_info["ip_address"],
        user_agent=client_info["user_agent"],
        status="success"
    )

    # Add owner name
    owner = db.query(User).filter(User.id == env.user_id).first()
    env.owner_name = owner.username if owner else "unknown"

    return env


@router.delete("/user-environments/{env_id}")
def delete_user_environment(
    env_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Delete a user environment"""
    # Cannot delete base environment
    if env_id == 0:
        raise HTTPException(status_code=400, detail="不能删除基础环境")

    env = db.query(UserEnvironment).filter(UserEnvironment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="环境未找到")

    # Check permissions - only owner or admin can delete
    if env.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权删除此环境")

    try:
        # Remove conda environment
        remove_cmd = f"conda env remove -n {env.env_name} -y"
        result = subprocess.run(
            remove_cmd.split(),
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "环境删除失败"
            raise HTTPException(status_code=500, detail=f"Conda环境删除失败: {error_msg}")

        # Remove from models.database
        db.delete(env)
        db.commit()

        # Log environment deletion
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="environment_delete",
            resource_type="user_environment",
            resource_id=env.id,
            details={
                "env_name": env.env_name,
                "display_name": env.display_name
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return {"message": "环境删除成功"}

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="环境删除超时")
    except HTTPException:
        raise
    except Exception as e:
        # Log failed environment deletion
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="environment_delete",
            resource_type="user_environment",
            resource_id=env.id,
            details={
                "env_name": env.env_name,
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"环境删除失败: {str(e)}")

# Admin endpoints for managing all user environments

@router.get("/admin/user-environments", response_model=list[UserEnvironmentResponse])
def admin_get_all_environments(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get all user environments (admin only)"""
    environments = db.query(UserEnvironment).all()
    for env in environments:
        owner = db.query(User).filter(User.id == env.user_id).first()
        env.owner_name = owner.username if owner else "unknown"
    return environments


@router.delete("/admin/user-environments/{env_id}")
def admin_delete_environment(
    env_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
    client_info: dict = Depends(get_client_info)
):
    """Admin can delete any user environment"""
    env = db.query(UserEnvironment).filter(UserEnvironment.id == env_id).first()
    if not env:
        raise HTTPException(status_code=404, detail="环境未找到")

    try:
        # Remove conda environment
        remove_cmd = f"conda env remove -n {env.env_name} -y"
        result = subprocess.run(
            remove_cmd.split(),
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "环境删除失败"
            raise HTTPException(status_code=500, detail=f"Conda环境删除失败: {error_msg}")

        # Remove from models.database
        db.delete(env)
        db.commit()

        # Log environment deletion
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="admin_environment_delete",
            resource_type="user_environment",
            resource_id=env.id,
            details={
                "env_name": env.env_name,
                "display_name": env.display_name,
                "original_owner_id": env.user_id
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return {"message": "环境删除成功"}

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="环境删除超时")
    except Exception as e:
        log_system_event(
            db=db,
            user_id=current_user.id,
            action="admin_environment_delete",
            resource_type="user_environment",
            resource_id=env.id,
            details={
                "env_name": env.env_name,
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"环境删除失败: {str(e)}")


@router.get("/environments/{env_name}/info")
def get_environment_info(
    env_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get information about a specific conda environment"""
    # Check if user has permission to access this environment
    if env_name != "base":
        # Check if it's a user environment
        user_env = db.query(UserEnvironment).filter(
            UserEnvironment.env_name == env_name,
            UserEnvironment.is_active == True
        ).first()

        if user_env:
            # Check permissions
            if (user_env.user_id != current_user.id and
                not user_env.is_public and
                not current_user.is_admin):
                raise HTTPException(status_code=403, detail="无权访问此环境")
        else:
            # If not in user environments, only admin can access system environments (except base)
            if not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权访问此环境")

            # Admin cannot access runner environment
            if env_name == "runner":
                raise HTTPException(status_code=403, detail="无权访问此环境")
    try:
        # Get Python version and environment info
        python_cmd = f"conda run -n {env_name} python" if env_name != "base" else "python"

        # Get Python version
        version_result = subprocess.run(
            f"{python_cmd} --version".split(),
            capture_output=True,
            text=True,
            timeout=10
        )

        python_version = version_result.stdout.strip() if version_result.returncode == 0 else "Unknown"

        # Get Python executable path
        path_result = subprocess.run(
            f"{python_cmd} -c \"import sys; print(sys.executable)\"".split(),
            capture_output=True,
            text=True,
            timeout=10
        )

        python_path = path_result.stdout.strip() if path_result.returncode == 0 else "Unknown"

        # Get site packages path
        site_packages_result = subprocess.run(
            f"{python_cmd} -c \"import site; print(site.getsitepackages()[0])\"".split(),
            capture_output=True,
            text=True,
            timeout=10
        )

        site_packages_path = site_packages_result.stdout.strip() if site_packages_result.returncode == 0 else "Unknown"

        # Count installed packages
        pip_list_result = subprocess.run(
            f"{python_cmd} -m pip list".split(),
            capture_output=True,
            text=True,
            timeout=15
        )

        package_count = 0
        if pip_list_result.returncode == 0:
            lines = pip_list_result.stdout.split('\n')
            for line in lines[2:]:  # Skip header lines
                if line.strip():
                    package_count += 1

        return {
            "name": env_name,
            "python_version": python_version,
            "python_path": python_path,
            "site_packages_path": site_packages_path,
            "package_count": package_count,
            "is_base": env_name == "base",
            "environment_type": "系统默认" if env_name == "base" else "虚拟环境"
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="获取环境信息超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取环境信息失败: {str(e)}")


@router.get("/environments/{env_name}/packages")
def get_environment_packages(
    env_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get packages installed in a specific conda environment"""
    # Check if user has permission to access this environment
    if env_name != "base":
        # Check if it's a user environment
        user_env = db.query(UserEnvironment).filter(
            UserEnvironment.env_name == env_name,
            UserEnvironment.is_active == True
        ).first()

        if user_env:
            # Check permissions
            if (user_env.user_id != current_user.id and
                not user_env.is_public and
                not current_user.is_admin):
                raise HTTPException(status_code=403, detail="无权访问此环境")
        else:
            # If not in user environments, only admin can access system environments (except base)
            if not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权访问此环境")

            # Admin cannot access runner environment
            if env_name == "runner":
                raise HTTPException(status_code=403, detail="无权访问此环境")
    try:
        # Get Python version and installed packages
        python_cmd = f"conda run -n {env_name} python" if env_name != "base" else "python"

        # Get Python version
        version_result = subprocess.run(
            f"{python_cmd} --version".split(),
            capture_output=True,
            text=True,
            timeout=10
        )

        python_version = version_result.stdout.strip() if version_result.returncode == 0 else "Unknown"

        # Get installed packages using pip list
        pip_list_result = subprocess.run(
            f"{python_cmd} -m pip list --format=json".split(),
            capture_output=True,
            text=True,
            timeout=30
        )

        if pip_list_result.returncode != 0:
            # Fallback to pip list without json format
            pip_list_result = subprocess.run(
                f"{python_cmd} -m pip list".split(),
                capture_output=True,
                text=True,
                timeout=30
            )

            if pip_list_result.returncode == 0:
                # Parse the output manually
                packages = []
                lines = pip_list_result.stdout.split('\n')
                for line in lines[2:]:  # Skip header lines
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 2:
                            package_name = parts[0]
                            version = parts[1]
                            packages.append({
                                "name": package_name,
                                "version": version,
                                "latest_version": None,
                                "size": None,
                                "location": None
                            })
                return packages

        # Parse JSON output
        import json
        packages_info = json.loads(pip_list_result.stdout)

        # Enhance package information
        packages = []
        for pkg in packages_info:
            packages.append({
                "name": pkg.get("name", ""),
                "version": pkg.get("version", ""),
                "latest_version": None,  # Could be implemented with pip list --outdated
                "size": None,  # Size info not available in basic pip list
                "location": None
            })

        return packages

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="获取包列表超时")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取包列表失败: {str(e)}")


@router.post("/environments/{env_name}/packages/install")
def install_package(
    env_name: str,
    package_data: dict,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    """Install a package in a specific conda environment"""
    # Check if user has permission to access this environment
    if env_name != "base":
        # Check if it's a user environment
        user_env = db.query(UserEnvironment).filter(
            UserEnvironment.env_name == env_name,
            UserEnvironment.is_active == True
        ).first()

        if user_env:
            # Check permissions - only owner or admin can install packages
            if user_env.user_id != current_user.id and not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权修改此环境")
        else:
            # If not in user environments, only admin can access system environments (except base)
            if not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权访问此环境")

            # Admin cannot install packages in runner environment
            if env_name == "runner":
                raise HTTPException(status_code=403, detail="无权修改此环境")
    try:
        # Protect base environment - only admins can modify it
        if env_name == "base" and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以修改基础环境")

        package_name = package_data.get("package_name", "")
        if not package_name:
            raise HTTPException(status_code=400, detail="请提供包名")

        # Validate package name format
        import re
        if not re.match(r'^[a-zA-Z0-9\-_.==>=<]+$', package_name):
            raise HTTPException(status_code=400, detail="包名格式无效")

        # Determine python command
        python_cmd = f"conda run -n {env_name} python" if env_name != "base" else "python"
        pip_cmd = f"conda run -n {env_name} pip" if env_name != "base" else "pip"

        # Install the package
        install_result = subprocess.run(
            f"{pip_cmd} install {package_name}".split(),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout for installation
        )

        if install_result.returncode != 0:
            error_msg = install_result.stderr.strip() if install_result.stderr else "安装失败"
            raise HTTPException(status_code=500, detail=f"包安装失败: {error_msg}")

        # Log the package installation
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_install",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "success": True
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return {"message": f"包 {package_name} 安装成功"}

    except subprocess.TimeoutExpired:
        # Log timeout
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_install",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "error": "timeout"
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=408, detail="包安装超时")
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_install",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"包安装失败: {str(e)}")


@router.delete("/environments/{env_name}/packages/{package_name}")
def uninstall_package(
    env_name: str,
    package_name: str,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    """Uninstall a package from a specific conda environment"""
    # Check if user has permission to access this environment
    if env_name != "base":
        # Check if it's a user environment
        user_env = db.query(UserEnvironment).filter(
            UserEnvironment.env_name == env_name,
            UserEnvironment.is_active == True
        ).first()

        if user_env:
            # Check permissions - only owner or admin can uninstall packages
            if user_env.user_id != current_user.id and not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权修改此环境")
        else:
            # If not in user environments, only admin can access system environments (except base)
            if not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权访问此环境")

            # Admin cannot uninstall packages in runner environment
            if env_name == "runner":
                raise HTTPException(status_code=403, detail="无权修改此环境")
    try:
        # Protect base environment - only admins can modify it
        if env_name == "base" and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以修改基础环境")

        # Validate package name
        import re
        if not re.match(r'^[a-zA-Z0-9\-_.]+$', package_name):
            raise HTTPException(status_code=400, detail="包名格式无效")

        # Don't allow uninstalling critical packages
        critical_packages = {"pip", "setuptools", "wheel", "python"}
        if package_name.lower() in critical_packages:
            raise HTTPException(status_code=400, detail=f"不能卸载关键包: {package_name}")

        # Determine pip command
        pip_cmd = f"conda run -n {env_name} pip" if env_name != "base" else "pip"

        # Uninstall the package
        uninstall_result = subprocess.run(
            f"{pip_cmd} uninstall -y {package_name}".split(),
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes timeout for uninstallation
        )

        if uninstall_result.returncode != 0:
            error_msg = uninstall_result.stderr.strip() if uninstall_result.stderr else "卸载失败"
            raise HTTPException(status_code=500, detail=f"包卸载失败: {error_msg}")

        # Log the package uninstallation
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_uninstall",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "success": True
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return {"message": f"包 {package_name} 卸载成功"}

    except subprocess.TimeoutExpired:
        # Log timeout
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_uninstall",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "error": "timeout"
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=408, detail="包卸载超时")
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_uninstall",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"包卸载失败: {str(e)}")


@router.put("/environments/{env_name}/packages/{package_name}/upgrade")
def upgrade_package(
    env_name: str,
    package_name: str,
    current_user: User = Depends(get_current_user),
    client_info: dict = Depends(get_client_info),
    db: Session = Depends(get_db)
):
    """Upgrade a package in a specific conda environment"""
    # Check if user has permission to access this environment
    if env_name != "base":
        # Check if it's a user environment
        user_env = db.query(UserEnvironment).filter(
            UserEnvironment.env_name == env_name,
            UserEnvironment.is_active == True
        ).first()

        if user_env:
            # Check permissions - only owner or admin can upgrade packages
            if user_env.user_id != current_user.id and not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权修改此环境")
        else:
            # If not in user environments, only admin can access system environments (except base)
            if not current_user.is_admin:
                raise HTTPException(status_code=403, detail="无权访问此环境")

            # Admin cannot upgrade packages in runner environment
            if env_name == "runner":
                raise HTTPException(status_code=403, detail="无权修改此环境")
    try:
        # Protect base environment - only admins can modify it
        if env_name == "base" and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="只有管理员可以修改基础环境")

        # Validate package name
        import re
        if not re.match(r'^[a-zA-Z0-9\-_.]+$', package_name):
            raise HTTPException(status_code=400, detail="包名格式无效")

        # Determine pip command
        pip_cmd = f"conda run -n {env_name} pip" if env_name != "base" else "pip"

        # Upgrade the package
        upgrade_result = subprocess.run(
            f"{pip_cmd} install --upgrade {package_name}".split(),
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout for upgrade
        )

        if upgrade_result.returncode != 0:
            error_msg = upgrade_result.stderr.strip() if upgrade_result.stderr else "升级失败"
            raise HTTPException(status_code=500, detail=f"包升级失败: {error_msg}")

        # Log the package upgrade
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_upgrade",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "success": True
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="success"
        )

        return {"message": f"包 {package_name} 升级成功"}

    except subprocess.TimeoutExpired:
        # Log timeout
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_upgrade",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "error": "timeout"
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=408, detail="包升级超时")
    except HTTPException:
        raise
    except Exception as e:
        # Log error
        log_system_event(
            db=next(get_db()),
            user_id=current_user.id,
            action="package_upgrade",
            resource_type="environment",
            details={
                "environment": env_name,
                "package_name": package_name,
                "error": str(e)
            },
            ip_address=client_info["ip_address"],
            user_agent=client_info["user_agent"],
            status="error"
        )
        raise HTTPException(status_code=500, detail=f"包升级失败: {str(e)}")

# User Profile endpoints

@router.get("/environments/available")
def get_available_environments(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get all available environments for the current user"""

    # User's own environments
    user_envs = db.query(UserEnvironment).filter(
        UserEnvironment.user_id == current_user.id,
        UserEnvironment.is_active == True
    ).all()

    # Public environments from other users
    public_envs = db.query(UserEnvironment).filter(
        UserEnvironment.is_public == True,
        UserEnvironment.is_active == True,
        UserEnvironment.user_id != current_user.id
    ).all()

    # Always include base environment
    environments = [{"name": "base", "display_name": "Base Environment", "is_default": True}]

    # Add user environments
    for env in user_envs:
        environments.append({
            "name": env.env_name,
            "display_name": env.display_name,
            "is_default": False
        })

    # Add public environments
    for env in public_envs:
        environments.append({
            "name": env.env_name,
            "display_name": f"{env.display_name} (by {env.user_id})",
            "is_default": False
        })

    return {"environments": environments}

# Delete Post API

