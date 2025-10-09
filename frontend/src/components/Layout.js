import React, { useState } from 'react';
import { Layout as AntLayout, Menu, Button, Typography, Space, Dropdown, Modal, Form, Input, message } from 'antd';
import { HomeOutlined, UserOutlined, LogoutOutlined, CodeOutlined, LoginOutlined, UserAddOutlined, BookOutlined, KeyOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';
import { changePassword } from '../services/api';

const { Header, Content, Footer } = AntLayout;
const { Title } = Typography;

const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [passwordForm] = Form.useForm();

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleChangePassword = async (values) => {
    try {
      await changePassword({
        current_password: values.currentPassword,
        new_password: values.newPassword
      });

      message.success('密码修改成功！');
      setPasswordModalVisible(false);
      passwordForm.resetFields();
    } catch (err) {
      message.error(err.response?.data?.detail || '密码修改失败');
    }
  };

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: 'Home',
    },
    {
      key: '/code-library',
      icon: <BookOutlined />,
      label: '代码库',
    },
  ];

  // Add Users menu item only for admin users
  if (user && user.is_admin) {
    menuItems.push({
      key: '/users',
      icon: <UserOutlined />,
      label: '用户管理',
    });
  }

  return (
    <AntLayout style={{ minHeight: '100vh' }}>
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        background: '#fff',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
        padding: '0 24px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <CodeOutlined style={{ fontSize: '24px', marginRight: '12px', color: '#1890ff' }} />
          <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
            CodeRunner
          </Title>
          {user && (
            <Menu
              mode="horizontal"
              selectedKeys={[location.pathname]}
              items={menuItems}
              onClick={handleMenuClick}
              style={{
                border: 'none',
                marginLeft: '32px',
                minWidth: '400px'
              }}
            />
          )}
        </div>

        <Space>
          {user ? (
            <Dropdown
              menu={{
                items: [
                  {
                    key: '1',
                    label: (
                      <span>
                        <UserOutlined style={{ marginRight: 8 }} />
                        {user?.full_name || user?.username}
                      </span>
                    ),
                    disabled: true,
                  },
                  {
                    type: 'divider',
                  },
                  {
                    key: '2',
                    icon: <KeyOutlined />,
                    label: '修改密码',
                    onClick: () => setPasswordModalVisible(true),
                  },
                  {
                    key: '3',
                    icon: <LogoutOutlined />,
                    label: '退出登录',
                    onClick: handleLogout,
                  },
                ],
              }}
              trigger={['click']}
            >
              <Button type="primary" icon={<UserOutlined />}>
                {user?.full_name || user?.username}
              </Button>
            </Dropdown>
          ) : (
            <>
              <Button
                icon={<LoginOutlined />}
                onClick={() => navigate('/login')}
              >
                Login
              </Button>
              <Button
                type="primary"
                icon={<UserAddOutlined />}
                onClick={() => navigate('/login')}
              >
                Sign Up
              </Button>
            </>
          )}
        </Space>
      </Header>

      <Content style={{ padding: '0', background: '#f0f2f5' }}>
        {children}
      </Content>

      <Footer style={{ textAlign: 'center', background: '#fff', borderTop: '1px solid #f0f0f0' }}>
        CodeRunner ©2024 - Remote Python Code Execution Platform
      </Footer>

      {/* Password Change Modal */}
      <Modal
        title="修改密码"
        open={passwordModalVisible}
        onCancel={() => {
          setPasswordModalVisible(false);
          passwordForm.resetFields();
        }}
        footer={null}
      >
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handleChangePassword}
        >
          <Form.Item
            name="currentPassword"
            label="当前密码"
            rules={[
              {
                required: true,
                message: '请输入当前密码！',
              },
            ]}
          >
            <Input.Password placeholder="请输入当前密码" />
          </Form.Item>

          <Form.Item
            name="newPassword"
            label="新密码"
            rules={[
              {
                required: true,
                message: '请输入新密码！',
              },
              {
                min: 6,
                message: '新密码至少需要6个字符！',
              },
            ]}
          >
            <Input.Password placeholder="请输入新密码（至少6个字符）" />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="确认新密码"
            dependencies={['newPassword']}
            rules={[
              {
                required: true,
                message: '请确认新密码！',
              },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致！'));
                },
              }),
            ]}
          >
            <Input.Password placeholder="请再次输入新密码" />
          </Form.Item>

          <Form.Item>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <Button
                onClick={() => {
                  setPasswordModalVisible(false);
                  passwordForm.resetFields();
                }}
              >
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                确认修改
              </Button>
            </div>
          </Form.Item>
        </Form>
      </Modal>
    </AntLayout>
  );
};

export default Layout;