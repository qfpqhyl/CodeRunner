import React from 'react';
import { Layout as AntLayout, Menu, Button, Typography, Space } from 'antd';
import { HomeOutlined, UserOutlined, LogoutOutlined, CodeOutlined, LoginOutlined, UserAddOutlined } from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';

const { Header, Content, Footer } = AntLayout;
const { Title } = Typography;

const Layout = ({ children }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: 'Home',
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
                minWidth: '200px'
              }}
            />
          )}
        </div>

        <Space>
          {user ? (
            <>
              <span style={{ color: '#666' }}>
                Welcome, {user?.full_name || user?.username}
              </span>
              <Button
                type="primary"
                icon={<LogoutOutlined />}
                onClick={handleLogout}
              >
                Logout
              </Button>
            </>
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
    </AntLayout>
  );
};

export default Layout;