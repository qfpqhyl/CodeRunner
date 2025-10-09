import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Typography, Space, Tag, Popconfirm, message, Modal, Form, Input, Switch } from 'antd';
import { UserOutlined, PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import { getUsers, createUser, updateUser, deleteUser } from '../services/api';
import { useAuth } from '../components/AuthContext';

const { Title } = Typography;

const UserManagement = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    loadUsers();
  }, []);

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
      <Card>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px'
        }}>
          <Title level={2}>
            <UserOutlined /> 用户管理
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

export default UserManagement;