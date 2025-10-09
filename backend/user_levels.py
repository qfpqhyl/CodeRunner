# User level configuration
USER_LEVELS = {
    1: {
        "name": "免费用户",
        "description": "基础功能，有限制",
        "max_execution_time": 30,  # seconds
        "max_memory": 128,  # MB
        "daily_executions": 10,
        "max_saved_codes": 5,  # codes in library
        "color": "#ff7875"
    },
    2: {
        "name": "基础用户",
        "description": "适合个人使用",
        "max_execution_time": 60,  # seconds
        "max_memory": 256,  # MB
        "daily_executions": 50,
        "max_saved_codes": 20,  # codes in library
        "color": "#ffa940"
    },
    3: {
        "name": "高级用户",
        "description": "适合开发者和团队",
        "max_execution_time": 120,  # seconds
        "max_memory": 512,  # MB
        "daily_executions": 200,
        "max_saved_codes": 100,  # codes in library
        "color": "#52c41a"
    },
    4: {
        "name": "企业用户",
        "description": "企业级功能和性能",
        "max_execution_time": 300,  # seconds
        "max_memory": 1024,  # MB
        "daily_executions": -1,  # unlimited
        "max_saved_codes": -1,  # unlimited codes in library
        "color": "#1890ff"
    }
}

def get_user_level_config(level: int):
    """Get user level configuration"""
    return USER_LEVELS.get(level, USER_LEVELS[1])

def get_daily_execution_count(user_id: int, db) -> int:
    """Get today's execution count for a user"""
    from datetime import date
    today = date.today()
    from database import CodeExecution

    count = db.query(CodeExecution).filter(
        CodeExecution.user_id == user_id,
        CodeExecution.created_at >= today
    ).count()

    return count

def can_user_execute(user, db) -> tuple[bool, str]:
    """Check if user can execute code based on their level limits"""
    if not user.is_active:
        return False, "用户账户已被禁用"

    level_config = get_user_level_config(user.user_level)

    # Check daily execution limit
    if level_config["daily_executions"] > 0:  # -1 means unlimited
        today_count = get_daily_execution_count(user.id, db)
        if today_count >= level_config["daily_executions"]:
            return False, f"今日执行次数已达上限 ({level_config['daily_executions']} 次)"

    return True, "可以执行"

def format_execution_count(count: int) -> str:
    """Format execution count for display"""
    return "无限制" if count == -1 else str(count)