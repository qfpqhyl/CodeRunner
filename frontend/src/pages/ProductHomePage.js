import React from 'react';
import { Card, Button, Typography, Row, Col, Space, Statistic, Alert } from 'antd';
import { PlayCircleOutlined, CodeOutlined, ThunderboltOutlined, SafetyOutlined,
         GlobalOutlined, ClockCircleOutlined, StarOutlined, RocketOutlined } from '@ant-design/icons';
import { useAuth } from '../components/AuthContext';

const { Title, Paragraph, Text } = Typography;

const ProductHomePage = () => {
  const { user } = useAuth();

  const features = [
    {
      icon: <ThunderboltOutlined style={{ fontSize: '32px', color: '#1890ff' }} />,
      title: '快速执行',
      description: '毫秒级响应，实时查看代码执行结果'
    },
    {
      icon: <SafetyOutlined style={{ fontSize: '32px', color: '#52c41a' }} />,
      title: '安全隔离',
      description: '沙箱环境运行，确保代码执行安全'
    },
    {
      icon: <GlobalOutlined style={{ fontSize: '32px', color: '#722ed1' }} />,
      title: '远程访问',
      description: '随时随地通过网络访问您的代码执行环境'
    },
    {
      icon: <ClockCircleOutlined style={{ fontSize: '32px', color: '#fa8c16' }} />,
      title: '历史记录',
      description: '保存执行历史，方便回顾和调试'
    }
  ];

  const examples = [
    {
      title: 'Hello World',
      code: 'print("Hello, World!")\nprint("Welcome to CodeRunner")'
    },
    {
      title: '数据处理',
      code: '# 数据分析示例\nimport json\n\ndata = {"name": "Python", "version": "3.9"}\nprint(json.dumps(data, indent=2))'
    },
    {
      title: '数学计算',
      code: '# 数学运算示例\nimport math\n\nradius = 5\narea = math.pi * radius ** 2\nprint(f"圆的面积: {area:.2f}")'
    }
  ];

  if (user) {
    // 已登录用户看到的首页
    return (
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px' }}>
        <Row gutter={[24, 24]}>
          <Col span={24}>
            <Card>
              <Title level={2}>
                <CodeOutlined /> 欢迎使用 CodeRunner
              </Title>
              <Paragraph>
                远端Python代码执行平台 - 开始编写和执行您的代码
              </Paragraph>
              <Space size="large">
                <Statistic
                  title="欢迎回来"
                  value={user?.full_name || user?.username}
                  prefix={<StarOutlined />}
                />
              </Space>
            </Card>
          </Col>

          {examples.map((example, index) => (
            <Col xs={24} md={8} key={index}>
              <Card
                title={example.title}
                size="small"
                extra={
                  <Button
                    type="primary"
                    icon={<PlayCircleOutlined />}
                    onClick={() => {
                      // 跳转到主页并加载示例代码
                      window.location.href = '/?example=' + encodeURIComponent(example.code);
                    }}
                  >
                    运行示例
                  </Button>
                }
              >
                <pre style={{
                  background: '#f5f5f5',
                  padding: '12px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  maxHeight: '150px',
                  overflow: 'auto',
                  margin: 0
                }}>
                  {example.code}
                </pre>
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    );
  }

  // 未登录用户看到的产品首页
  return (
    <div>
      {/* Hero Section */}
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '80px 24px',
        textAlign: 'center',
        color: 'white'
      }}>
        <div style={{ maxWidth: 800, margin: '0 auto' }}>
          <Title level={1} style={{ color: 'white', marginBottom: '16px' }}>
            <RocketOutlined /> CodeRunner
          </Title>
          <Title level={3} style={{ color: 'white', fontWeight: 400, marginBottom: '32px' }}>
            远端Python代码执行平台
          </Title>
          <Paragraph style={{ fontSize: '18px', color: 'rgba(255,255,255,0.9)', marginBottom: '40px' }}>
            随时随地安全执行Python代码，实时查看结果，保存执行历史
          </Paragraph>
          <Space size="large">
            <Button
              type="primary"
              size="large"
              icon={<PlayCircleOutlined />}
              onClick={() => window.location.href = '/login'}
              style={{
                background: 'white',
                color: '#667eea',
                border: 'none',
                height: '48px',
                padding: '0 32px',
                fontSize: '16px'
              }}
            >
              免费开始使用
            </Button>
            <Button
              size="large"
              style={{
                background: 'transparent',
                color: 'white',
                border: '1px solid white',
                height: '48px',
                padding: '0 32px',
                fontSize: '16px'
              }}
            >
              了解更多
            </Button>
          </Space>
        </div>
      </div>

      {/* Features Section */}
      <div style={{ padding: '80px 24px', background: '#fff' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '60px' }}>
            <Title level={2}>为什么选择 CodeRunner？</Title>
            <Paragraph style={{ fontSize: '16px', color: '#666' }}>
              专业、安全、高效的代码执行平台
            </Paragraph>
          </div>

          <Row gutter={[32, 32]}>
            {features.map((feature, index) => (
              <Col xs={24} md={12} lg={6} key={index}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ marginBottom: '16px' }}>
                    {feature.icon}
                  </div>
                  <Title level={4}>{feature.title}</Title>
                  <Paragraph style={{ color: '#666' }}>
                    {feature.description}
                  </Paragraph>
                </div>
              </Col>
            ))}
          </Row>
        </div>
      </div>

      {/* Examples Section */}
      <div style={{ padding: '80px 24px', background: '#f8f9fa' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '60px' }}>
            <Title level={2}>代码示例</Title>
            <Paragraph style={{ fontSize: '16px', color: '#666' }}>
              查看一些常见的Python代码执行示例
            </Paragraph>
          </div>

          <Row gutter={[24, 24]}>
            {examples.map((example, index) => (
              <Col xs={24} md={8} key={index}>
                <Card
                  title={example.title}
                  size="small"
                  style={{ height: '100%' }}
                >
                  <pre style={{
                    background: '#f5f5f5',
                    padding: '16px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    maxHeight: '200px',
                    overflow: 'auto',
                    margin: '0 0 16px 0'
                  }}>
                    {example.code}
                  </pre>
                  <Alert
                    message="登录后即可运行代码"
                    type="info"
                    showIcon
                    action={
                      <Button
                        type="primary"
                        size="small"
                        onClick={() => window.location.href = '/login'}
                      >
                        立即登录
                      </Button>
                    }
                  />
                </Card>
              </Col>
            ))}
          </Row>
        </div>
      </div>

      {/* CTA Section */}
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '60px 24px',
        textAlign: 'center',
        color: 'white'
      }}>
        <div style={{ maxWidth: 600, margin: '0 auto' }}>
          <Title level={2} style={{ color: 'white', marginBottom: '16px' }}>
            准备好开始了吗？
          </Title>
          <Paragraph style={{ fontSize: '16px', color: 'rgba(255,255,255,0.9)', marginBottom: '32px' }}>
            立即注册，免费使用 CodeRunner 平台执行您的 Python 代码
          </Paragraph>
          <Button
            type="primary"
            size="large"
            icon={<RocketOutlined />}
            onClick={() => window.location.href = '/login'}
            style={{
              background: 'white',
              color: '#667eea',
              border: 'none',
              height: '48px',
              padding: '0 32px',
              fontSize: '16px'
            }}
          >
            免费注册
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ProductHomePage;