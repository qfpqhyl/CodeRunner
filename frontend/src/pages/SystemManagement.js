import { useState, useEffect, useCallback } from 'react';
import { Card, Table, Button, Typography, Space, Tag, Popconfirm, message, Modal, Form, Input, Switch, Select, Tabs, DatePicker, Row, Col, Statistic, Spin, Empty, Tooltip } from 'antd';
import { UserOutlined, PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined, FileTextOutlined, BarChartOutlined, FilterOutlined, ExportOutlined, SettingOutlined } from '@ant-design/icons';
import { getUsers, createUser, updateUser, deleteUser, getUserLevels, getSystemLogs, getLogStatistics, getLogActions, getLogResourceTypes } from '../services/api';
import moment from 'moment';
import { useAuth } from '../components/AuthContext';

const { Title } = Typography;
const { Option } = Select;

const SystemManagement = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [userLevels, setUserLevels] = useState({});
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [form] = Form.useForm();

  // Logs related state
  const [activeTab, setActiveTab] = useState('users');
  const [logs, setLogs] = useState([]);
  const [logStats, setLogStats] = useState({});
  const [logActions, setLogActions] = useState([]);
  const [logResourceTypes, setLogResourceTypes] = useState([]);
  const [logsLoading, setLogsLoading] = useState(false);
  const [filtersVisible, setFiltersVisible] = useState(false);

  // Filter state
  const [logFilters, setLogFilters] = useState({
    action: null,
    resource_type: null,
    status: null,
    user_id: null,
    start_date: null,
    end_date: null
  });

  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0
  });

  useEffect(() => {
    loadUsers();
    loadUserLevels();
  }, []);

  useEffect(() => {
    if (activeTab === 'logs') {
      loadLogData();
    }
  }, [activeTab]);

  const loadUserLevels = async () => {
    try {
      const response = await getUserLevels();
      setUserLevels(response.data);
    } catch (error) {
      message.error('加载用户等级配置失败');
    }
  };

  // Move loadLogs function before the useEffect that uses it
  const loadLogs = useCallback(async () => {
    setLogsLoading(true);
    try {
      const params = {
        limit: pagination.pageSize,
        offset: (pagination.current - 1) * pagination.pageSize,
        ...Object.fromEntries(
          Object.entries(logFilters).filter(([_, value]) => value !== null && value !== undefined && value !== '')
        )
      };

      // Convert dates to ISO format
      if (params.start_date) {
        params.start_date = params.start_date.toISOString();
      }
      if (params.end_date) {
        params.end_date = params.end_date.toISOString();
      }

      const response = await getSystemLogs(params);
      setLogs(response.data);
    } catch (error) {
      message.error('加载日志失败');
    } finally {
      setLogsLoading(false);
    }
  }, [logFilters, pagination]);

  // Add useEffect to reload logs when dependencies change
  useEffect(() => {
    if (activeTab === 'logs') {
      loadLogs();
    }
  }, [activeTab, loadLogs]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await getUsers();
      setUsers(response.data);
    } catch (error) {
      if (error.response?.status === 403) {
        message.error('您没有权限访问用户管理功能');
      } else {
        message.error('加载用户列表失败');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (user) => {
    setEditingUser(user);
    form.setFieldsValue({
      username: user.username,
      email: user.email,
      full_name: user.full_name,
      is_admin: user.is_admin,
      is_active: user.is_active,
      user_level: user.user_level,
      password: '' // Don't populate password for security
    });
    setModalVisible(true);
  };

  const handleDelete = async (userId) => {
    try {
      await deleteUser(userId);
      message.success('用户删除成功');
      loadUsers();
    } catch (error) {
      message.error('删除用户失败: ' + (error.response?.data?.detail || '未知错误'));
    }
  };

  const handleSubmit = async (values) => {
    try {
      if (editingUser) {
        // Update existing user
        const updateData = { ...values };
        if (!updateData.password) {
          delete updateData.password; // Don't update password if empty
        }
        await updateUser(editingUser.id, updateData);
        message.success('用户更新成功');
      } else {
        // Create new user
        await createUser(values);
        message.success('用户创建成功');
      }
      setModalVisible(false);
      loadUsers();
    } catch (error) {
      message.error('操作失败: ' + (error.response?.data?.detail || '未知错误'));
    }
  };

  // Log related functions
  const loadLogData = async () => {
    try {
      const [statsRes, actionsRes, resourceTypesRes] = await Promise.all([
        getLogStatistics({ days: 7 }),
        getLogActions(),
        getLogResourceTypes()
      ]);

      setLogStats(statsRes.data);
      setLogActions(actionsRes.data);
      setLogResourceTypes(resourceTypesRes.data);
    } catch (error) {
      message.error('加载日志数据失败');
    }
  };

  // Add useEffect to reload logs when pagination or filters change
  useEffect(() => {
    if (activeTab === 'logs') {
      loadLogs();
    }
  }, [activeTab, pagination, loadLogs]);

  const handleFilterChange = (field, value) => {
    setLogFilters(prev => ({ ...prev, [field]: value }));
    setPagination(prev => ({ ...prev, current: 1 })); // Reset to first page
  };

  const clearFilters = () => {
    setLogFilters({
      action: null,
      resource_type: null,
      status: null,
      user_id: null,
      start_date: null,
      end_date: null
    });
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const exportLogs = () => {
    // Create CSV content
    const headers = ['时间', '用户', '操作', '资源类型', '状态', 'IP地址', '详情'];
    const csvContent = [
      headers.join(','),
      ...logs.map(log => [
        moment(log.created_at).format('YYYY-MM-DD HH:mm:ss'),
        log.user?.username || '系统',
        log.action,
        log.resource_type,
        log.status,
        log.ip_address,
        JSON.stringify(log.details || '').replace(/"/g, '""')
      ].map(field => `"${field}"`).join(','))
    ].join('\n');

    // Download CSV file
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `system_logs_${moment().format('YYYY-MM-DD')}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const logColumns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (date) => moment(date).format('MM-DD HH:mm:ss'),
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
    },
    {
      title: '用户',
      dataIndex: 'user',
      key: 'user',
      width: 120,
      render: (user) => user ? (
        <Space>
          <span>{user.username}</span>
          {user.full_name && (
            <Tooltip title={user.full_name}>
              <span style={{ color: '#999' }}>({user.full_name})</span>
            </Tooltip>
          )}
        </Space>
      ) : (
        <Tag color="default">系统</Tag>
      ),
    },
    {
      title: '操作',
      dataIndex: 'action',
      key: 'action',
      width: 140,
      render: (action) => {
        const actionColors = {
          user_login: 'blue',
          user_register: 'green',
          user_logout: 'orange',
          code_execute: 'purple',
          user_create: 'cyan',
          user_update: 'geekblue',
          user_delete: 'red',
          api_call: 'magenta',
          password_change: 'volcano',
        };
        return (
          <Tag color={actionColors[action] || 'default'}>
            {action}
          </Tag>
        );
      },
    },
    {
      title: '资源类型',
      dataIndex: 'resource_type',
      key: 'resource_type',
      width: 100,
      render: (type) => type && <Tag color="default">{type}</Tag>,
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status) => {
        const statusColors = {
          success: 'green',
          error: 'red',
          warning: 'orange',
        };
        return (
          <Tag color={statusColors[status] || 'default'}>
            {status}
          </Tag>
        );
      },
    },
    {
      title: 'IP地址',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 120,
      render: (ip) => ip && <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>{ip}</span>,
    },
    {
      title: '详情',
      dataIndex: 'details',
      key: 'details',
      render: (details) => {
        if (!details) return '-';

        // Display key details in a readable format
        const displayDetails = [];
        if (details.status) displayDetails.push(`状态: ${details.status}`);
        if (details.execution_time) displayDetails.push(`耗时: ${details.execution_time}ms`);
        if (details.code_length) displayDetails.push(`代码: ${details.code_length}字符`);
        if (details.username) displayDetails.push(`用户: ${details.username}`);
        if (details.reason) displayDetails.push(`原因: ${details.reason}`);

        const summary = displayDetails.join(', ') || JSON.stringify(details);

        return (
          <Tooltip title={JSON.stringify(details, null, 2)}>
            <span style={{
              maxWidth: '200px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              display: 'inline-block'
            }}>
              {summary}
            </span>
          </Tooltip>
        );
      },
    },
  ];

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      sorter: (a, b) => a.id - b.id,
      width: 80,
    },
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      render: (text, record) => (
        <Space>
          <UserOutlined />
          <span>{text}</span>
          {record.id === currentUser?.id && (
            <Tag color="blue">当前用户</Tag>
          )}
          {record.is_admin && (
            <Tag color="red">管理员</Tag>
          )}
        </Space>
      ),
    },
    {
      title: '全名',
      dataIndex: 'full_name',
      key: 'full_name',
      render: (text) => text || '-',
    },
    {
      title: '邮箱',
      dataIndex: 'email',
      key: 'email',
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? '活跃' : '禁用'}
        </Tag>
      ),
    },
    {
      title: '用户等级',
      dataIndex: 'user_level',
      key: 'user_level',
      render: (level) => {
        const levelConfig = userLevels[level] || {};
        return (
          <Tag color={levelConfig.color || 'default'}>
            {levelConfig.name || `等级 ${level}`}
          </Tag>
        );
      },
    },
    {
      title: '角色',
      dataIndex: 'is_admin',
      key: 'is_admin',
      render: (isAdmin) => (
        <Tag color={isAdmin ? 'red' : 'blue'}>
          {isAdmin ? '管理员' : '普通用户'}
        </Tag>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleString(),
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size="small"
          >
            编辑
          </Button>
          {record.id !== currentUser?.id && (
            <Popconfirm
              title="确定要删除这个用户吗？"
              description="删除后无法恢复"
              onConfirm={() => handleDelete(record.id)}
              okText="确定"
              cancelText="取消"
            >
              <Button
                type="link"
                danger
                icon={<DeleteOutlined />}
                size="small"
              >
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto', padding: '24px' }}>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'users',
            label: (
              <span>
                <SettingOutlined />
                用户管理
              </span>
            ),
            children: (
              <Card>
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '16px'
                }}>
                  <Title level={2}>
                    <SettingOutlined /> 用户管理
                  </Title>
                  <Space>
                    <Button
                      icon={<ReloadOutlined />}
                      onClick={loadUsers}
                      loading={loading}
                    >
                      刷新
                    </Button>
                    <Button
                      type="primary"
                      icon={<PlusOutlined />}
                      onClick={handleCreate}
                    >
                      新建用户
                    </Button>
                  </Space>
                </div>

                <Table
                  columns={columns}
                  dataSource={users}
                  loading={loading}
                  rowKey="id"
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) =>
                      `${range[0]}-${range[1]} 共 ${total} 个用户`,
                  }}
                  scroll={{ x: 1200 }}
                />
              </Card>
            )
          },
          {
            key: 'logs',
            label: (
              <span>
                <FileTextOutlined />
                系统日志
              </span>
            ),
            children: (
              <div>
                {/* Statistics Cards */}
                {logStats.total_logs !== undefined && (
                  <Row gutter={16} style={{ marginBottom: 24 }}>
                    <Col span={6}>
                      <Card>
                        <Statistic
                          title="总日志数"
                          value={logStats.total_logs}
                          prefix={<BarChartOutlined />}
                          valueStyle={{ color: '#1890ff' }}
                        />
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card>
                        <Statistic
                          title="成功操作"
                          value={logStats.status_distribution?.success || 0}
                          prefix={<span style={{ color: '#52c41a' }}>✓</span>}
                          valueStyle={{ color: '#52c41a' }}
                        />
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card>
                        <Statistic
                          title="错误操作"
                          value={logStats.status_distribution?.error || 0}
                          prefix={<span style={{ color: '#f5222d' }}>✗</span>}
                          valueStyle={{ color: '#f5222d' }}
                        />
                      </Card>
                    </Col>
                    <Col span={6}>
                      <Card>
                        <Statistic
                          title="警告操作"
                          value={logStats.status_distribution?.warning || 0}
                          prefix={<span style={{ color: '#fa8c16' }}>⚠</span>}
                          valueStyle={{ color: '#fa8c16' }}
                        />
                      </Card>
                    </Col>
                  </Row>
                )}

                <Card>
                  <div style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '16px'
                  }}>
                    <Title level={2}>
                      <FileTextOutlined /> 系统日志
                    </Title>
                    <Space>
                      <Button
                        icon={<FilterOutlined />}
                        onClick={() => setFiltersVisible(!filtersVisible)}
                      >
                        {filtersVisible ? '隐藏过滤' : '显示过滤'}
                      </Button>
                      <Button
                        icon={<ReloadOutlined />}
                        onClick={loadLogs}
                        loading={logsLoading}
                      >
                        刷新
                      </Button>
                      <Button
                        icon={<ExportOutlined />}
                        onClick={exportLogs}
                        disabled={logs.length === 0}
                      >
                        导出CSV
                      </Button>
                    </Space>
                  </div>

                  {/* Filters */}
                  {filtersVisible && (
                    <Card
                      size="small"
                      style={{ marginBottom: 16, backgroundColor: '#fafafa' }}
                      title="筛选条件"
                    >
                      <Row gutter={16}>
                        <Col span={4}>
                          <Select
                            placeholder="操作类型"
                            style={{ width: '100%' }}
                            allowClear
                            value={logFilters.action}
                            onChange={(value) => handleFilterChange('action', value)}
                          >
                            {logActions.map(action => (
                              <Option key={action} value={action}>{action}</Option>
                            ))}
                          </Select>
                        </Col>
                        <Col span={4}>
                          <Select
                            placeholder="资源类型"
                            style={{ width: '100%' }}
                            allowClear
                            value={logFilters.resource_type}
                            onChange={(value) => handleFilterChange('resource_type', value)}
                          >
                            {logResourceTypes.map(type => (
                              <Option key={type} value={type}>{type}</Option>
                            ))}
                          </Select>
                        </Col>
                        <Col span={4}>
                          <Select
                            placeholder="状态"
                            style={{ width: '100%' }}
                            allowClear
                            value={logFilters.status}
                            onChange={(value) => handleFilterChange('status', value)}
                          >
                            <Option value="success">成功</Option>
                            <Option value="error">错误</Option>
                            <Option value="warning">警告</Option>
                          </Select>
                        </Col>
                        <Col span={4}>
                          <DatePicker
                            placeholder="开始日期"
                            style={{ width: '100%' }}
                            value={logFilters.start_date}
                            onChange={(value) => handleFilterChange('start_date', value)}
                          />
                        </Col>
                        <Col span={4}>
                          <DatePicker
                            placeholder="结束日期"
                            style={{ width: '100%' }}
                            value={logFilters.end_date}
                            onChange={(value) => handleFilterChange('end_date', value)}
                          />
                        </Col>
                        <Col span={4}>
                          <Button onClick={clearFilters}>清除筛选</Button>
                        </Col>
                      </Row>
                    </Card>
                  )}

                  <Table
                    columns={logColumns}
                    dataSource={logs}
                    loading={logsLoading}
                    rowKey="id"
                    pagination={{
                      current: pagination.current,
                      pageSize: pagination.pageSize,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total, range) =>
                        `${range[0]}-${range[1]} 共 ${total} 条日志`,
                      onChange: (page, pageSize) => {
                        setPagination(prev => ({ ...prev, current: page, pageSize }));
                      }
                    }}
                    scroll={{ x: 1200 }}
                    locale={{
                      emptyText: logsLoading ? (
                        <div style={{ padding: '40px' }}>
                          <Spin size="large" />
                          <div style={{ marginTop: 16 }}>加载日志中...</div>
                        </div>
                      ) : (
                        <Empty
                          description="暂无日志数据"
                          image={Empty.PRESENTED_IMAGE_SIMPLE}
                        />
                      )
                    }}
                  />
                </Card>
              </div>
            )
          }
        ]}
      />

      <Modal
        title={editingUser ? '编辑用户' : '新建用户'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' }
            ]}
          >
            <Input placeholder="输入用户名" />
          </Form.Item>

          <Form.Item
            name="email"
            label="邮箱"
            rules={[
              { required: true, message: '请输入邮箱' },
              { type: 'email', message: '请输入有效的邮箱地址' }
            ]}
          >
            <Input placeholder="输入邮箱地址" />
          </Form.Item>

          <Form.Item
            name="full_name"
            label="全名"
          >
            <Input placeholder="输入全名（可选）" />
          </Form.Item>

          <Form.Item
            name="password"
            label={editingUser ? "新密码（留空则不修改）" : "密码"}
            rules={editingUser ? [] : [
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' }
            ]}
          >
            <Input.Password placeholder="输入密码" />
          </Form.Item>

          <Form.Item
            name="is_admin"
            label="用户角色"
            valuePropName="checked"
          >
            <Switch checkedChildren="管理员" unCheckedChildren="普通用户" />
          </Form.Item>

          <Form.Item
            name="user_level"
            label="用户等级"
            rules={[{ required: true, message: '请选择用户等级' }]}
          >
            <Select placeholder="选择用户等级">
              {Object.entries(userLevels).map(([level, config]) => (
                <Option key={level} value={parseInt(level)}>
                  <span style={{ color: config.color }}>
                    {config.name} - {config.description}
                  </span>
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="is_active"
            label="用户状态"
            valuePropName="checked"
          >
            <Switch checkedChildren="活跃" unCheckedChildren="禁用" />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingUser ? '更新' : '创建'}
              </Button>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SystemManagement;