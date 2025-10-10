import React, { useState, useEffect } from 'react';
import { Card, Form, Input, Button, Typography, Alert, Tabs, Layout, theme, Space } from 'antd';
import {
  UserOutlined,
  LockOutlined,
  MailOutlined,
  CodeOutlined,
  SettingOutlined,
  BookOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import { register, login, getCurrentUser, getCurrentBackendUrl } from '../services/api';
import { useAuth } from '../components/AuthContext';
import DeploymentTutorial from '../components/DeploymentTutorial';
import BackendConfig from '../components/BackendConfig';

const { Title } = Typography;
const { Sider, Content } = Layout;

const LoginPage = () => {
  const { login: authLogin } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('login');
  const [backendConfigured, setBackendConfigured] = useState(false);
  const [showConfigPanel, setShowConfigPanel] = useState(true);

  const {
    token: { colorBgContainer },
  } = theme.useToken();

  useEffect(() => {
    // Check if backend is already configured
    const currentUrl = getCurrentBackendUrl();
    // Only consider configured if it's a valid HTTP URL that's not the default localhost
    if (currentUrl && currentUrl.startsWith('http') && currentUrl !== 'http://localhost:8000') {
      setBackendConfigured(true);
    } else {
      // Reset to default if invalid or default value
      setBackendConfigured(false);
      // Clear invalid backend URL from localStorage
      if (currentUrl === '/api' || !currentUrl || !currentUrl.startsWith('http')) {
        localStorage.removeItem('backendUrl');
      }
    }
  }, []);

  const onLogin = async (values) => {
    setLoading(true);
    setError('');

    try {
      const response = await login(values);
      // Store token first
      localStorage.setItem('token', response.data.access_token);
      // Then get user data with token
      const userData = await getCurrentUser();
      authLogin(response.data.access_token, userData.data);
    } catch (err) {
      setError(err.response?.data?.detail || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  const onRegister = async (values) => {
    setLoading(true);
    setError('');

    try {
      await register(values);
      // After successful registration, login
      const loginResponse = await login({
        username: values.username,
        password: values.password
      });
      // Store token first
      localStorage.setItem('token', loginResponse.data.access_token);
      // Then get user data with token
      const userData = await getCurrentUser();
      authLogin(loginResponse.data.access_token, userData.data);
    } catch (err) {
      setError(err.response?.data?.detail || '注册失败');
    } finally {
      setLoading(false);
    }
  };

  const handleBackendConfigured = () => {
    setBackendConfigured(true);
    setError('');
  };

  const toggleConfigPanel = () => {
    setShowConfigPanel(!showConfigPanel);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* 左侧：部署教程 */}
      {showConfigPanel && (
        <Sider
          width={600}
          style={{
            background: colorBgContainer,
            borderRight: '1px solid #f0f0f0',
            overflow: 'auto'
          }}
        >
          <DeploymentTutorial />
        </Sider>
      )}

      {/* 右侧：登录界面 */}
      <Layout style={{ flex: 1 }}>
        <Content style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #f8fafc 100%)',
          position: 'relative',
          overflow: 'hidden',
          padding: '20px'
        }}>
          {/* Background decoration */}
          <div style={{
            position: 'absolute',
            top: '-200px',
            right: '-200px',
            width: '500px',
            height: '500px',
            background: 'radial-gradient(circle, rgba(24, 144, 255, 0.15) 0%, transparent 70%)',
            borderRadius: '50%'
          }} />
          <div style={{
            position: 'absolute',
            bottom: '-150px',
            left: '-150px',
            width: '400px',
            height: '400px',
            background: 'radial-gradient(circle, rgba(114, 46, 209, 0.1) 0%, transparent 70%)',
            borderRadius: '50%'
          }} />

          <div style={{ width: '100%', maxWidth: 480, position: 'relative', zIndex: 1 }}>
            {/* 切换按钮 */}
            <div style={{ textAlign: 'center', marginBottom: 20 }}>
              <Button
                type="text"
                onClick={toggleConfigPanel}
                style={{
                  color: '#1890ff',
                  border: '1px solid #d9d9d9',
                  borderRadius: '20px',
                  padding: '4px 16px'
                }}
              >
                {showConfigPanel ? (
                  <>
                    <SettingOutlined /> 隐藏部署教程
                  </>
                ) : (
                  <>
                    <BookOutlined /> 显示部署教程
                  </>
                )}
              </Button>
            </div>

            <Card style={{
              boxShadow: '0 20px 60px rgba(0,0,0,0.08)',
              borderRadius: '24px',
              border: '1px solid #e2e8f0',
              background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
            }}>
              <div style={{ textAlign: 'center', marginBottom: 40, paddingTop: 30 }}>
                <div style={{
                  marginBottom: 20,
                  fontSize: '48px',
                  background: 'linear-gradient(135deg, #1890ff, #722ed1)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent'
                }}>
                  <CodeOutlined />
                </div>
                <Title level={1} style={{
                  color: '#1e293b',
                  marginBottom: '8px',
                  fontSize: '2em',
                  fontWeight: 'bold',
                  letterSpacing: '-1px'
                }}>
                  CodeRunner
                </Title>
                <p style={{
                  color: '#64748b',
                  fontSize: '16px',
                  margin: 0
                }}>
                  远端Python代码执行平台
                </p>
              </div>

              {/* 后端配置状态提示 */}
              {backendConfigured && (
                <Alert
                  message={
                    <Space>
                      <CheckCircleOutlined style={{ color: '#52c41a' }} />
                      <span>后端服务已连接</span>
                    </Space>
                  }
                  type="success"
                  showIcon={false}
                  style={{
                    marginBottom: 24,
                    borderRadius: '12px',
                    border: '1px solid #b7eb8f',
                    background: '#f6ffed'
                  }}
                  action={
                    <Button
                      type="text"
                      size="small"
                      onClick={() => setBackendConfigured(false)}
                    >
                      重新配置
                    </Button>
                  }
                />
              )}

              {error && (
                <Alert
                  message={error}
                  type="error"
                  showIcon
                  style={{
                    marginBottom: 24,
                    borderRadius: '12px',
                    border: '1px solid #fee2e2',
                    background: '#fef2f2'
                  }}
                />
              )}

              {!backendConfigured ? (
                <BackendConfig onConfigured={handleBackendConfigured} />
              ) : (
                <Tabs
                  activeKey={activeTab}
                  onChange={setActiveTab}
                  centered
                  size="large"
                  style={{
                    marginBottom: 30
                  }}
                  items={[
                    {
                      key: 'login',
                      label: '登录',
                      children: (
                        <Form name="login" onFinish={onLogin} layout="vertical">
                          <Form.Item
                            name="username"
                            rules={[{ required: true, message: '请输入用户名!' }]}
                          >
                            <Input
                              prefix={<UserOutlined style={{ color: '#1890ff' }} />}
                              placeholder="用户名"
                              size="large"
                              style={{
                                borderRadius: '12px',
                                padding: '12px 16px',
                                fontSize: '16px',
                                border: '1px solid #e2e8f0'
                              }}
                            />
                          </Form.Item>

                          <Form.Item
                            name="password"
                            rules={[{ required: true, message: '请输入密码!' }]}
                          >
                            <Input.Password
                              prefix={<LockOutlined style={{ color: '#1890ff' }} />}
                              placeholder="密码"
                              size="large"
                              style={{
                                borderRadius: '12px',
                                padding: '12px 16px',
                                fontSize: '16px',
                                border: '1px solid #e2e8f0'
                              }}
                            />
                          </Form.Item>

                          <Form.Item style={{ marginBottom: 0 }}>
                            <Button
                              type="primary"
                              htmlType="submit"
                              loading={loading}
                              size="large"
                              block
                              style={{
                                height: '50px',
                                borderRadius: '12px',
                                background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
                                border: 'none',
                                fontSize: '16px',
                                fontWeight: '600',
                                boxShadow: '0 4px 12px rgba(24, 144, 255, 0.3)',
                                transition: 'all 0.3s ease'
                              }}
                            >
                              登录
                            </Button>
                          </Form.Item>
                        </Form>
                      )
                    },
                    {
                      key: 'register',
                      label: '注册',
                      children: (
                        <Form name="register" onFinish={onRegister} layout="vertical">
                          <Form.Item
                            name="username"
                            rules={[{ required: true, message: '请输入用户名!' }]}
                          >
                            <Input
                              prefix={<UserOutlined style={{ color: '#1890ff' }} />}
                              placeholder="用户名"
                              size="large"
                              style={{
                                borderRadius: '12px',
                                padding: '12px 16px',
                                fontSize: '16px',
                                border: '1px solid #e2e8f0'
                              }}
                            />
                          </Form.Item>

                          <Form.Item
                            name="email"
                            rules={[
                              { required: true, message: '请输入邮箱!' },
                              { type: 'email', message: '请输入有效的邮箱地址!' }
                            ]}
                          >
                            <Input
                              prefix={<MailOutlined style={{ color: '#1890ff' }} />}
                              placeholder="邮箱"
                              size="large"
                              style={{
                                borderRadius: '12px',
                                padding: '12px 16px',
                                fontSize: '16px',
                                border: '1px solid #e2e8f0'
                              }}
                            />
                          </Form.Item>

                          <Form.Item
                            name="full_name"
                          >
                            <Input
                              placeholder="姓名 (可选)"
                              size="large"
                              style={{
                                borderRadius: '12px',
                                padding: '12px 16px',
                                fontSize: '16px',
                                border: '1px solid #e2e8f0'
                              }}
                            />
                          </Form.Item>

                          <Form.Item
                            name="password"
                            rules={[
                              { required: true, message: '请输入密码!' },
                              { min: 6, message: '密码至少需要6个字符!' }
                            ]}
                          >
                            <Input.Password
                              prefix={<LockOutlined style={{ color: '#1890ff' }} />}
                              placeholder="密码"
                              size="large"
                              style={{
                                borderRadius: '12px',
                                padding: '12px 16px',
                                fontSize: '16px',
                                border: '1px solid #e2e8f0'
                              }}
                            />
                          </Form.Item>

                          <Form.Item style={{ marginBottom: 0 }}>
                            <Button
                              type="primary"
                              htmlType="submit"
                              loading={loading}
                              size="large"
                              block
                              style={{
                                height: '50px',
                                borderRadius: '12px',
                                background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
                                border: 'none',
                                fontSize: '16px',
                                fontWeight: '600',
                                boxShadow: '0 4px 12px rgba(24, 144, 255, 0.3)',
                                transition: 'all 0.3s ease'
                              }}
                            >
                              注册
                            </Button>
                          </Form.Item>
                        </Form>
                      )
                    }
                  ]}
                />
              )}
            </Card>
          </div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default LoginPage;