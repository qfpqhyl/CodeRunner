import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Typography,
  Row,
  Col,
  Tag,
  Button,
  Space,
  Table,
  Modal,
  Form,
  Input,
  message,
  Alert,
  Spin,
  Empty,
  Tooltip,
  Popconfirm,
  List,
  Switch,
  Select
} from 'antd';
import {
  DesktopOutlined,
  CodeOutlined,
  AppstoreOutlined,
  InfoCircleOutlined,
  DeleteOutlined,
  PlusOutlined,
  ReloadOutlined,
  UserOutlined,
  LockOutlined,
  UnlockOutlined
} from '@ant-design/icons';
import {
  getCondaEnvironments,
  getEnvironmentPackages,
  getEnvironmentInfo,
  installPackage,
  uninstallPackage,
  upgradePackage,
  getUserEnvironments,
  createUserEnvironment,
  deleteUserEnvironment,
  getCurrentUser
} from '../services/api';

const { Title, Paragraph, Text } = Typography;
const { Search } = Input;

const EnvironmentPage = () => {
  const [environments, setEnvironments] = useState([]);
  const [environmentsInfo, setEnvironmentsInfo] = useState({});
  const [userEnvironments, setUserEnvironments] = useState([]);
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedEnv, setSelectedEnv] = useState(null);
  const [packages, setPackages] = useState([]);
  const [packagesLoading, setPackagesLoading] = useState(false);
  const [installModalVisible, setInstallModalVisible] = useState(false);
  const [createEnvModalVisible, setCreateEnvModalVisible] = useState(false);
  const [installForm] = Form.useForm();
  const [createEnvForm] = Form.useForm();
  const [searchText, setSearchText] = useState('');
  const [canCreateEnvironment, setCanCreateEnvironment] = useState(true);

  // 加载环境信息
  const loadEnvironmentInfo = useCallback(async (envName) => {
    try {
      const response = await getEnvironmentInfo(envName);
      setEnvironmentsInfo(prev => ({
        ...prev,
        [envName]: response.data
      }));
    } catch (error) {
      console.error(`Failed to load environment info for ${envName}:`, error);
      // 不显示错误信息，因为这不是关键功能
    }
  }, []);

  // 加载当前用户信息
  const loadCurrentUser = useCallback(async () => {
    try {
      const response = await getCurrentUser();
      setCurrentUser(response.data);

      // 检查用户是否可以创建环境（普通用户只能创建一个）
      if (!response.data.is_admin) {
        const userEnvsResponse = await getUserEnvironments();
        const userEnvs = userEnvsResponse.data.filter(env => env.user_id === response.data.id && env.env_name !== 'base');
        setCanCreateEnvironment(userEnvs.length === 0);
      }
    } catch (error) {
      console.error('Failed to load current user:', error);
    }
  }, []);

  // 加载用户环境列表
  const loadUserEnvironments = useCallback(async () => {
    try {
      const response = await getUserEnvironments();
      setUserEnvironments(response.data);
    } catch (error) {
      console.error('Failed to load user environments:', error);
    }
  }, []);

  // 加载conda环境列表
  const loadEnvironments = useCallback(async () => {
    setLoading(true);
    try {
      const response = await getCondaEnvironments();
      // 过滤掉runner环境
      const filteredEnvs = response.data.filter(env => env !== 'runner');
      setEnvironments(filteredEnvs);

      // 加载所有环境的信息
      for (const env of filteredEnvs) {
        await loadEnvironmentInfo(env);
      }

      // 如果没有选中环境，默认选择第一个
      if (!selectedEnv && filteredEnvs.length > 0) {
        setSelectedEnv(filteredEnvs[0]);
      }
    } catch (error) {
      console.error('Failed to load environments:', error);
      message.error('加载环境列表失败');
    } finally {
      setLoading(false);
    }
  }, [selectedEnv, loadEnvironmentInfo]);

  // 加载指定环境的包列表
  const loadPackages = useCallback(async (envName) => {
    if (!envName) return;

    setPackagesLoading(true);
    try {
      const response = await getEnvironmentPackages(envName);
      setPackages(response.data || []);
    } catch (error) {
      console.error('Failed to load packages:', error);
      message.error(`加载环境 ${envName} 的包列表失败`);
      setPackages([]);
    } finally {
      setPackagesLoading(false);
    }
  }, []);

  // 初始化加载
  useEffect(() => {
    const initializeData = async () => {
      await Promise.all([
        loadCurrentUser(),
        loadUserEnvironments(),
        loadEnvironments()
      ]);
    };
    initializeData();
  }, [loadCurrentUser, loadUserEnvironments, loadEnvironments]);

  // 当选中的环境改变时，加载对应的包列表
  useEffect(() => {
    if (selectedEnv) {
      loadPackages(selectedEnv);
    }
  }, [selectedEnv, loadPackages]);

  // 安装包
  const handleInstallPackage = async (values) => {
    try {
      await installPackage(selectedEnv, values.package_name);
      message.success(`包 ${values.package_name} 安装成功`);
      setInstallModalVisible(false);
      installForm.resetFields();
      loadPackages(selectedEnv); // 重新加载包列表
    } catch (error) {
      message.error(error.response?.data?.detail || '包安装失败');
    }
  };

  // 卸载包
  const handleUninstallPackage = async (packageName) => {
    try {
      await uninstallPackage(selectedEnv, packageName);
      message.success(`包 ${packageName} 卸载成功`);
      loadPackages(selectedEnv); // 重新加载包列表
    } catch (error) {
      message.error(error.response?.data?.detail || '包卸载失败');
    }
  };

  // 升级包
  const handleUpgradePackage = async (packageName) => {
    try {
      await upgradePackage(selectedEnv, packageName);
      message.success(`包 ${packageName} 升级成功`);
      loadPackages(selectedEnv); // 重新加载包列表
    } catch (error) {
      message.error(error.response?.data?.detail || '包升级失败');
    }
  };

  // 创建用户环境
  const handleCreateEnvironment = async (values) => {
    try {
      const envData = {
        env_name: values.env_name,
        display_name: values.display_name,
        description: values.description,
        python_version: values.python_version,
        is_public: values.is_public || false,
        packages: values.packages ? values.packages.split(',').map(pkg => pkg.trim()).filter(pkg => pkg) : []
      };

      await createUserEnvironment(envData);
      message.success(`环境 ${values.display_name || values.env_name} 创建成功`);
      setCreateEnvModalVisible(false);
      createEnvForm.resetFields();

      // 重新加载环境和用户环境列表
      await Promise.all([
        loadEnvironments(),
        loadUserEnvironments(),
        loadCurrentUser()
      ]);
    } catch (error) {
      message.error(error.response?.data?.detail || '环境创建失败');
    }
  };

  // 删除用户环境
  const handleDeleteEnvironment = async (envId, envName) => {
    try {
      await deleteUserEnvironment(envId);
      message.success(`环境 ${envName} 删除成功`);

      // 如果删除的是当前选中的环境，切换到base环境
      if (selectedEnv === envName) {
        setSelectedEnv('base');
      }

      // 重新加载环境和用户环境列表
      await Promise.all([
        loadEnvironments(),
        loadUserEnvironments(),
        loadCurrentUser()
      ]);
    } catch (error) {
      message.error(error.response?.data?.detail || '环境删除失败');
    }
  };

  // 获取环境状态标签颜色
  const getEnvironmentTagColor = (envName) => {
    if (envName === 'base') return 'default';
    return 'processing';
  };

  // 过滤包列表
  const filteredPackages = packages.filter(pkg =>
    pkg.name.toLowerCase().includes(searchText.toLowerCase())
  );

  // 检查当前用户是否可以修改选中的环境
  const canModifyPackage = React.useMemo(() => {
    if (!selectedEnv || !currentUser) return false;

    // 只有管理员可以修改base环境
    if (selectedEnv === 'base') return currentUser.is_admin;

    // 查找用户环境信息
    const userEnv = userEnvironments.find(ue => ue.env_name === selectedEnv);
    if (!userEnv) return false; // 如果不是用户环境，只有管理员可以修改

    // 环境所有者或管理员可以修改
    return userEnv.user_id === currentUser.id || currentUser.is_admin;
  }, [selectedEnv, currentUser, userEnvironments]);

  // 包列表表格列配置
  const packageColumns = [
    {
      title: '包名',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <div>
          <Text strong>{text}</Text>
          {record.latest_version && record.version !== record.latest_version && (
            <Tag color="orange" style={{ marginLeft: 8 }}>
              可升级: {record.latest_version}
            </Tag>
          )}
        </div>
      ),
    },
    {
      title: '当前版本',
      dataIndex: 'version',
      key: 'version',
      width: 120,
      render: (version) => <Tag color="blue">{version}</Tag>,
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 100,
      render: (size) => size ? `${(size / 1024 / 1024).toFixed(1)}MB` : '-',
    },
    {
      title: '安装位置',
      dataIndex: 'location',
      key: 'location',
      width: 200,
      ellipsis: true,
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space size="small">
          {record.latest_version && record.version !== record.latest_version && (
            <Tooltip title="升级包">
              <Button
                type="text"
                icon={<ReloadOutlined />}
                onClick={() => handleUpgradePackage(record.name)}
                size="small"
              />
            </Tooltip>
          )}
          <Popconfirm
            title="确定要卸载这个包吗？"
            description={`这将从 ${selectedEnv} 环境中卸载 ${record.name}`}
            onConfirm={() => handleUninstallPackage(record.name)}
            okText="确定"
            cancelText="取消"
          >
            <Tooltip title="卸载包">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                size="small"
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '24px' }}>
      <Row gutter={[24, 24]}>
        {/* 页面标题 */}
        <Col span={24}>
          <Card>
            <Title level={2}>
              <DesktopOutlined /> 环境管理
            </Title>
            <Paragraph>
              管理Conda虚拟环境，查看环境信息，管理Python包依赖
            </Paragraph>
          </Card>
        </Col>

        {/* 环境列表 */}
        <Col xs={24} lg={8}>
          <Card
            title="Conda环境"
            extra={
              <Space>
                {canCreateEnvironment && (
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setCreateEnvModalVisible(true)}
                    size="small"
                  >
                    创建环境
                  </Button>
                )}
                <Button
                  icon={<ReloadOutlined />}
                  onClick={loadEnvironments}
                  loading={loading}
                  size="small"
                >
                  刷新
                </Button>
              </Space>
            }
          >
            <Spin spinning={loading}>
              {environments.length > 0 ? (
                <List
                  dataSource={environments}
                  renderItem={(env) => {
                    // 查找用户环境信息
                    const userEnv = userEnvironments.find(ue => ue.env_name === env);
                    const isUserEnv = userEnv && userEnv.id !== 0; // id为0是base环境
                    const isOwner = userEnv && currentUser && userEnv.user_id === currentUser.id;
                    const canDelete = isUserEnv && (isOwner || (currentUser && currentUser.is_admin));

                    return (
                      <List.Item
                        style={{
                          padding: '12px 16px',
                          cursor: 'pointer',
                          background: selectedEnv === env ? '#f0f9ff' : 'transparent',
                          borderRadius: '6px',
                          marginBottom: '8px',
                          border: selectedEnv === env ? '1px solid #1890ff' : '1px solid #f0f0f0'
                        }}
                        onClick={() => setSelectedEnv(env)}
                        actions={canDelete ? [
                          <Popconfirm
                            title="确定要删除这个环境吗？"
                            description={`删除环境 ${env} 将移除所有已安装的包`}
                            onConfirm={(e) => {
                              e.stopPropagation();
                              handleDeleteEnvironment(userEnv.id, env);
                            }}
                            okText="确定"
                            cancelText="取消"
                          >
                            <Button
                              type="text"
                              danger
                              icon={<DeleteOutlined />}
                              size="small"
                              onClick={(e) => e.stopPropagation()}
                            />
                          </Popconfirm>
                        ] : []}
                      >
                        <List.Item.Meta
                          avatar={
                            <div style={{
                              width: '40px',
                              height: '40px',
                              borderRadius: '50%',
                              background: env === 'base' ? '#f0f0f0' : (isUserEnv ? '#52c41a' : '#1890ff'),
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              color: env === 'base' ? '#666' : '#fff'
                            }}>
                              {env === 'base' ? <DesktopOutlined /> : isUserEnv ? <UserOutlined /> : <DesktopOutlined />}
                            </div>
                          }
                          title={
                            <Space>
                              <Text strong>{env}</Text>
                              <Tag color={getEnvironmentTagColor(env)}>
                                {environmentsInfo[env]?.environment_type || (env === 'base' ? '默认' : (isUserEnv ? '个人' : '虚拟'))}
                              </Tag>
                              {isUserEnv && (
                                <Tag color={userEnv.is_public ? 'green' : 'blue'} icon={userEnv.is_public ? <UnlockOutlined /> : <LockOutlined />}>
                                  {userEnv.is_public ? '公开' : '私有'}
                                </Tag>
                              )}
                            </Space>
                          }
                          description={
                            <Space direction="vertical" size="small">
                              {userEnv && userEnv.display_name && (
                                <Text style={{ fontSize: '12px', color: '#1890ff' }}>
                                  {userEnv.display_name}
                                </Text>
                              )}
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                <CodeOutlined style={{ marginRight: 4 }} />
                                {environmentsInfo[env]?.python_version || 'Python 版本获取中...'}
                              </Text>
                              <Text type="secondary" style={{ fontSize: '12px' }}>
                                <AppstoreOutlined style={{ marginRight: 4 }} />
                                {environmentsInfo[env]?.package_count || 0} 个已安装包
                              </Text>
                              {userEnv && userEnv.owner_name && (
                                <Text type="secondary" style={{ fontSize: '11px' }}>
                                  <UserOutlined style={{ marginRight: 4 }} />
                                  创建者: {userEnv.owner_name}
                                </Text>
                              )}
                              {environmentsInfo[env]?.site_packages_path && (
                                <Text type="secondary" style={{ fontSize: '11px' }} ellipsis>
                                  <InfoCircleOutlined style={{ marginRight: 4 }} />
                                  {environmentsInfo[env].site_packages_path}
                                </Text>
                              )}
                            </Space>
                          }
                        />
                      </List.Item>
                    );
                  }}
                />
              ) : (
                <Empty
                  description="暂无可用环境"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              )}
            </Spin>
          </Card>
        </Col>

        {/* 包管理区域 */}
        <Col xs={24} lg={16}>
          <Card
            title={
              <Space>
                <AppstoreOutlined />
                <span>{selectedEnv ? `${selectedEnv} 环境包管理` : '选择环境'}</span>
              </Space>
            }
            extra={
              selectedEnv && (
                <Space>
                  <Button
                    type="primary"
                    icon={<PlusOutlined />}
                    onClick={() => setInstallModalVisible(true)}
                    size="small"
                    disabled={!canModifyPackage}
                  >
                    安装包
                  </Button>
                  <Button
                    icon={<ReloadOutlined />}
                    onClick={() => loadPackages(selectedEnv)}
                    loading={packagesLoading}
                    size="small"
                  >
                    刷新
                  </Button>
                </Space>
              )
            }
          >
            {selectedEnv ? (
              <>
                <Alert
                  message="包管理说明"
                  description={
                    <div>
                      <div>正在管理 {selectedEnv} 环境的Python包。安装、卸载和升级操作将只影响当前环境。</div>
                      {!canModifyPackage && (
                        <div style={{ color: '#ff4d4f', marginTop: 4 }}>
                          您没有权限修改此环境。只有环境所有者或管理员可以修改包。
                        </div>
                      )}
                    </div>
                  }
                  type={canModifyPackage ? "info" : "warning"}
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                <Search
                  placeholder="搜索包名..."
                  allowClear
                  enterButton
                  value={searchText}
                  onChange={(e) => setSearchText(e.target.value)}
                  style={{ marginBottom: 16 }}
                />

                <Table
                  dataSource={filteredPackages}
                  columns={packageColumns}
                  rowKey="name"
                  loading={packagesLoading}
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total) => `共 ${total} 个包`,
                  }}
                  locale={{
                    emptyText: searchText ? '没有找到匹配的包' : '暂无已安装的包'
                  }}
                />
              </>
            ) : (
              <Empty
                description="请选择一个环境来管理包"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            )}
          </Card>
        </Col>
      </Row>

      {/* 安装包模态框 */}
      <Modal
        title="安装Python包"
        open={installModalVisible}
        onCancel={() => {
          setInstallModalVisible(false);
          installForm.resetFields();
        }}
        footer={null}
        width={500}
      >
        <Form
          form={installForm}
          layout="vertical"
          onFinish={handleInstallPackage}
        >
          <Alert
            message="安装说明"
            description={`将在 ${selectedEnv} 环境中安装指定的Python包。支持pip包名、版本号（如 package==1.0.0）和git地址。`}
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Form.Item
            name="package_name"
            label="包名"
            rules={[
              { required: true, message: '请输入包名' },
              { pattern: /^[a-zA-Z0-9\-_.==>=<]+$/, message: '请输入有效的包名' }
            ]}
          >
            <Input
              placeholder="例如：numpy, pandas==1.5.0, git+https://github.com/user/repo.git"
              addonAfter={
                <Tooltip title="支持包名、版本约束、git地址等pip支持的格式">
                  <InfoCircleOutlined style={{ color: '#999' }} />
                </Tooltip>
              }
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => {
                setInstallModalVisible(false);
                installForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                安装
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 创建环境模态框 */}
      <Modal
        title="创建新环境"
        open={createEnvModalVisible}
        onCancel={() => {
          setCreateEnvModalVisible(false);
          createEnvForm.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={createEnvForm}
          layout="vertical"
          onFinish={handleCreateEnvironment}
        >
          <Alert
            message="环境创建说明"
            description={
              <div>
                <div>• 普通用户只能创建一个个人环境</div>
                <div>• 环境名称只能包含字母、数字、下划线和连字符</div>
                <div>• 创建完成后将自动安装指定的Python包</div>
                {currentUser && currentUser.is_admin && (
                  <div style={{ color: '#1890ff' }}>• 管理员可以创建多个环境</div>
                )}
              </div>
            }
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
          />

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="env_name"
                label="环境名称"
                rules={[
                  { required: true, message: '请输入环境名称' },
                  { pattern: /^[a-zA-Z0-9_-]+$/, message: '环境名称只能包含字母、数字、下划线和连字符' }
                ]}
              >
                <Input placeholder="例如: myenv, project_dev" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="display_name"
                label="显示名称"
                rules={[
                  { required: true, message: '请输入显示名称' }
                ]}
              >
                <Input placeholder="例如: 我的环境" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="python_version"
            label="Python版本"
            rules={[{ required: true, message: '请选择Python版本' }]}
            initialValue="3.11"
          >
            <Select>
              <Select.Option value="3.9">Python 3.9</Select.Option>
              <Select.Option value="3.10">Python 3.10</Select.Option>
              <Select.Option value="3.11">Python 3.11</Select.Option>
              <Select.Option value="3.12">Python 3.12</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="描述"
          >
            <Input.TextArea
              placeholder="描述这个环境的用途..."
              rows={2}
              maxLength={200}
              showCount
            />
          </Form.Item>

          <Form.Item
            name="packages"
            label="初始包（可选）"
            tooltip="请输入要安装的包名，用逗号分隔。例如：numpy, pandas, matplotlib"
          >
            <Input
              placeholder="例如：numpy, pandas, matplotlib"
              addonAfter={
                <Tooltip title="用逗号分隔多个包名，支持pip包名和版本号">
                  <InfoCircleOutlined style={{ color: '#999' }} />
                </Tooltip>
              }
            />
          </Form.Item>

          <Form.Item
            name="is_public"
            label="公开环境"
            valuePropName="checked"
            initialValue={false}
            tooltip="公开环境可以被其他用户使用，但不能被修改"
          >
            <Switch
              checkedChildren="公开"
              unCheckedChildren="私有"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => {
                setCreateEnvModalVisible(false);
                createEnvForm.resetFields();
              }}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                创建环境
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default EnvironmentPage;