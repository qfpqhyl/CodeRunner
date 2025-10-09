import React, { useState, useEffect } from 'react';
import { Card, Button, Typography, Row, Col, Space, Statistic, Alert } from 'antd';
import { PlayCircleOutlined, CodeOutlined, ThunderboltOutlined, SafetyOutlined,
         GlobalOutlined, ClockCircleOutlined, StarOutlined, RocketOutlined, BookOutlined } from '@ant-design/icons';
import { useAuth } from '../components/AuthContext';

const { Title, Paragraph, Text } = Typography;

const ProductHomePage = () => {
  const { user } = useAuth();
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentExample, setCurrentExample] = useState(0);

  // 定义示例数据
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

  // 模拟代码执行动画
  const simulateExecution = () => {
    setIsExecuting(true);
    setTimeout(() => {
      setIsExecuting(false);
    }, 2000);
  };

  // 自动切换示例代码
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentExample((prev) => (prev + 1) % examples.length);
    }, 5000);
    return () => clearInterval(interval);
  }, [examples.length]);

  // 滚动到指定部分
  const scrollToSection = (sectionId) => {
    const section = document.getElementById(sectionId);
    if (section) {
      section.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // 滚动到下一个部分
  const scrollToNext = () => {
    scrollToSection('product-showcase');
  };

  // 添加CSS动画样式
  useEffect(() => {
    const style = document.createElement('style');
    style.textContent = `
      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }
      @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
      }
      @keyframes bounce {
        0%, 20%, 50%, 80%, 100% { transform: translateY(0); }
        40% { transform: translateY(-10px); }
        60% { transform: translateY(-5px); }
      }
      @keyframes float {
        0%, 100% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
      }
    `;
    document.head.appendChild(style);
    return () => {
      document.head.removeChild(style);
    };
  }, []);

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
                <pre className="code-editor" style={{
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
        background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #f8fafc 100%)',
        height: '100vh',
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden',
        padding: '24px'
      }}>
        {/* 背景装饰元素 */}
        <div style={{
          position: 'absolute',
          top: '-100px',
          right: '-100px',
          width: '300px',
          height: '300px',
          background: 'radial-gradient(circle, rgba(24, 144, 255, 0.1) 0%, transparent 70%)',
          borderRadius: '50%'
        }} />
        <div style={{
          position: 'absolute',
          bottom: '-150px',
          left: '-150px',
          width: '400px',
          height: '400px',
          background: 'radial-gradient(circle, rgba(114, 46, 209, 0.08) 0%, transparent 70%)',
          borderRadius: '50%'
        }} />

        <div style={{ maxWidth: 1200, margin: '0 auto', position: 'relative', zIndex: 1 }}>
          <div style={{ marginBottom: '40px' }}>
            <Title level={1} style={{
              color: '#1e293b',
              marginBottom: '16px',
              fontSize: '3.5em',
              fontWeight: 'bold',
              letterSpacing: '-1px'
            }}>
              <CodeOutlined style={{
                marginRight: '16px',
                color: '#1890ff',
                background: 'linear-gradient(135deg, #1890ff, #722ed1)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }} />
              CodeRunner
            </Title>
            <Title level={3} style={{
              color: '#475569',
              fontWeight: 400,
              marginBottom: '24px',
              fontSize: '1.6em',
              letterSpacing: '0.5px'
            }}>
              远端Python代码执行平台
            </Title>
            <Paragraph style={{
              fontSize: '18px',
              color: '#64748b',
              marginBottom: '40px',
              maxWidth: '700px',
              margin: '0 auto 40px',
              lineHeight: '1.6'
            }}>
              安全、快速、易用的Python代码执行环境。支持代码保存、API调用、执行历史记录，满足个人和团队的开发需求。
            </Paragraph>
          </div>

          <Space size="large">
            <Button
              type="primary"
              size="large"
              icon={<PlayCircleOutlined />}
              onClick={() => window.location.href = '/login'}
              style={{
                background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
                border: 'none',
                height: '52px',
                padding: '0 40px',
                fontSize: '17px',
                borderRadius: '26px',
                fontWeight: '600',
                boxShadow: '0 6px 20px rgba(24, 144, 255, 0.3)',
                transition: 'all 0.3s ease'
              }}
            >
              免费开始使用
            </Button>
            <Button
              size="large"
              onClick={scrollToNext}
              style={{
                background: 'white',
                color: '#1890ff',
                border: '2px solid #1890ff',
                height: '52px',
                padding: '0 40px',
                fontSize: '17px',
                borderRadius: '26px',
                fontWeight: '600',
                transition: 'all 0.3s ease'
              }}
            >
              了解更多
            </Button>
          </Space>
        </div>

        </div>

      {/* Product Showcase Section */}
      <div
        id="product-showcase"
        style={{
          padding: '80px 24px',
          background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
          position: 'relative'
        }}>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          <div style={{
            textAlign: 'center',
            marginBottom: '60px'
          }}>
            <Title level={2} style={{
              color: '#1e293b',
              marginBottom: '12px',
              fontSize: '2.2em',
              fontWeight: 'bold'
            }}>
              平台界面展示
            </Title>
            <Paragraph style={{
              fontSize: '18px',
              color: '#475569',
              maxWidth: '700px',
              margin: '0 auto',
              lineHeight: '1.6'
            }}>
              专业的左右布局设计，左侧代码编辑器，右侧实时显示执行结果
            </Paragraph>
          </div>

          <Row gutter={[32, 32]} justify="center" align="middle">
            {/* 左侧：代码编辑器区域 */}
            <Col xs={24} lg={12}>
              <div style={{
                background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                borderRadius: '20px',
                padding: '30px',
                boxShadow: '0 25px 70px rgba(0,0,0,0.15)',
                border: '1px solid #334155',
                position: 'relative',
                overflow: 'hidden',
                height: '500px'
              }}>
                {/* 编辑器标题栏 */}
                <div style={{
                  background: 'rgba(51, 65, 85, 0.5)',
                  borderRadius: '12px',
                  padding: '15px 20px',
                  marginBottom: '20px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  backdropFilter: 'blur(10px)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      background: '#ef4444',
                      boxShadow: '0 0 10px rgba(239, 68, 68, 0.5)'
                    }} />
                    <div style={{
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      background: '#f59e0b',
                      boxShadow: '0 0 10px rgba(245, 158, 11, 0.5)'
                    }} />
                    <div style={{
                      width: '12px',
                      height: '12px',
                      borderRadius: '50%',
                      background: '#10b981',
                      boxShadow: '0 0 10px rgba(16, 185, 129, 0.5)'
                    }} />
                  </div>
                  <Text style={{
                    color: '#94a3b8',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}>
                    main.py
                  </Text>
                </div>

                {/* 代码内容 */}
                <div style={{
                  fontFamily: 'monospace',
                  fontSize: '14px',
                  lineHeight: '1.7',
                  color: '#e2e8f0',
                  height: 'calc(100% - 80px)',
                  overflow: 'auto',
                  whiteSpace: 'pre-wrap',
                  opacity: isExecuting ? 0.7 : 1,
                  transition: 'opacity 0.3s ease'
                }}>
                  {examples[currentExample].code.split('\n').map((line, index) => (
                    <div key={index}>
                      {line.includes('import') && (
                        <><span style={{ color: '#f472b6' }}>import</span> {line.replace('import', '')}</>
                      )}
                      {line.includes('#') && (
                        <span style={{ color: '#64748b' }}>{line}</span>
                      )}
                      {line.includes('print') && line.includes('(') && (
                        <>
                          <span style={{ color: '#f472b6' }}>print</span>(
                          <span style={{ color: '#86efac' }}>{line.split('(')[1].split(')')[0]}</span>)
                        </>
                      )}
                      {line.includes('=') && !line.includes('import') && !line.includes('#') && !line.includes('print') && (
                        <>
                          {line.split('=')[0]}= <span style={{ color: '#60a5fa' }}>{line.split('=')[1]}</span>
                        </>
                      )}
                      {line.includes('response.') && (
                        <>
                          response.<span style={{ color: '#60a5fa' }}>{line.split('.')[1]}</span>
                        </>
                      )}
                      {line.includes('if') || line.includes('else') ? (
                        <span style={{ color: '#f472b6' }}>{line}</span>
                      ) : line.includes('import') || line.includes('#') || line.includes('print') ||
                         line.includes('=') || line.includes('response.') ? null : (
                        <span>{line}</span>
                      )}
                    </div>
                  ))}
                </div>

                {/* 运行按钮 */}
                <div style={{
                  position: 'absolute',
                  bottom: '30px',
                  right: '30px',
                  display: 'flex',
                  gap: '12px'
                }}>
                  <Button
                    size="large"
                    onClick={() => setCurrentExample((prev) => (prev + 1) % examples.length)}
                    style={{
                      background: 'rgba(255, 255, 255, 0.1)',
                      border: '1px solid rgba(255, 255, 255, 0.2)',
                      borderRadius: '12px',
                      fontWeight: '600',
                      color: 'white'
                    }}
                  >
                    切换示例
                  </Button>
                  <Button
                    type="primary"
                    size="large"
                    icon={isExecuting ? <div style={{ animation: 'spin 1s linear infinite' }}>⟳</div> : <PlayCircleOutlined />}
                    onClick={simulateExecution}
                    disabled={isExecuting}
                    style={{
                      background: isExecuting ? '#64748b' : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                      border: 'none',
                      borderRadius: '12px',
                      fontWeight: '600',
                      boxShadow: isExecuting ? 'none' : '0 8px 24px rgba(16, 185, 129, 0.4)',
                      minWidth: '120px'
                    }}
                  >
                    {isExecuting ? '执行中...' : '运行代码'}
                  </Button>
                </div>
              </div>
            </Col>

            {/* 右侧：执行结果区域 */}
            <Col xs={24} lg={12}>
              <div style={{
                background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                borderRadius: '20px',
                padding: '30px',
                boxShadow: '0 25px 70px rgba(0,0,0,0.08)',
                border: '1px solid #e2e8f0',
                height: '500px',
                display: 'flex',
                flexDirection: 'column'
              }}>
                {/* 结果标题栏 */}
                <div style={{
                  background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
                  borderRadius: '12px',
                  padding: '15px 20px',
                  marginBottom: '20px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  borderBottom: '1px solid #e2e8f0'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      width: '10px',
                      height: '10px',
                      borderRadius: '50%',
                      background: isExecuting ? '#f59e0b' : '#10b981',
                      animation: isExecuting ? 'pulse 1s infinite' : 'none'
                    }} />
                    <Text style={{
                      fontSize: '16px',
                      fontWeight: '600',
                      color: '#1e293b'
                    }}>
                      {isExecuting ? '执行中...' : '执行结果'}
                    </Text>
                  </div>
                  <div style={{ display: 'flex', gap: '15px' }}>
                    <Text style={{ color: '#64748b', fontSize: '14px' }}>
                      <ClockCircleOutlined /> 执行时间: 0.23s
                    </Text>
                    <Text style={{ color: '#64748b', fontSize: '14px' }}>
                      内存: 15.2MB
                    </Text>
                  </div>
                </div>

                {/* 结果内容 */}
                <div style={{
                  flex: 1,
                  background: '#f8fafc',
                  borderRadius: '12px',
                  padding: '20px',
                  fontFamily: 'monospace',
                  fontSize: '14px',
                  lineHeight: '1.6',
                  color: '#1e293b',
                  overflow: 'auto',
                  border: '1px solid #e2e8f0'
                }}>
                  <div style={{ marginBottom: '16px' }}>
                    <span style={{ color: '#10b981', fontWeight: '600' }}>$</span> python main.py
                  </div>
                  {isExecuting ? (
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      color: '#64748b',
                      fontStyle: 'italic'
                    }}>
                      <div style={{
                        width: '20px',
                        height: '20px',
                        border: '2px solid #3b82f6',
                        borderTop: '2px solid transparent',
                        borderRadius: '50%',
                        animation: 'spin 1s linear infinite'
                      }} />
                      正在执行代码...
                    </div>
                  ) : (
                    <>
                      <div style={{ marginBottom: '16px' }}>
                        <span style={{ color: '#3b82f6' }}>
                          {examples[currentExample].title === 'Hello World' && 'Hello, World!'}
                          {examples[currentExample].title === '数据处理' && '获取到数据:'}
                          {examples[currentExample].title === '数学计算' && '计算结果:'}
                        </span>
                      </div>
                      <pre style={{
                        background: '#1e293b',
                        color: '#f1f5f9',
                        padding: '16px',
                        borderRadius: '8px',
                        margin: 0,
                        fontSize: '13px',
                        overflow: 'auto'
                      }}>
                        {examples[currentExample].title === 'Hello World' && `Hello, World!
Welcome to CodeRunner`}
                        {examples[currentExample].title === '数据处理' && `{
  "name": "Python",
  "version": "3.9",
  "features": ["数据处理", "Web开发", "AI/机器学习"]
}`}
                        {examples[currentExample].title === '数学计算' && `圆的面积: 78.54
计算精度: 2位小数`}
                      </pre>
                    </>
                  )}
                </div>

                {/* 状态指示器 */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginTop: '20px',
                  padding: '15px',
                  background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)',
                  borderRadius: '12px',
                  border: '1px solid #bbf7d0'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: '#10b981'
                    }} />
                    <Text style={{ color: '#166534', fontWeight: '600' }}>
                      执行成功
                    </Text>
                  </div>
                  <Text style={{ color: '#64748b', fontSize: '13px' }}>
                    2024-01-15 10:30:00
                  </Text>
                </div>
              </div>
            </Col>
          </Row>

          {/* 特性标签 */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '20px',
            marginTop: '50px',
            flexWrap: 'wrap'
          }}>
            {[
              { icon: <ThunderboltOutlined />, text: '实时执行', color: '#3b82f6' },
              { icon: <SafetyOutlined />, text: '安全沙箱', color: '#10b981' },
              { icon: <BookOutlined />, text: '代码保存', color: '#8b5cf6' },
              { icon: <GlobalOutlined />, text: 'API支持', color: '#f59e0b' }
            ].map((tag, index) => (
              <div
                key={index}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 20px',
                  background: 'white',
                  borderRadius: '25px',
                  boxShadow: '0 4px 15px rgba(0,0,0,0.08)',
                  border: '1px solid #e2e8f0'
                }}
              >
                <span style={{ color: tag.color, fontSize: '16px' }}>
                  {tag.icon}
                </span>
                <Text style={{ color: '#1e293b', fontWeight: '500' }}>
                  {tag.text}
                </Text>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Advanced Features Section */}
      <div
        id="features"
        style={{
          padding: '80px 24px',
          background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)'
        }}>
        <div style={{ maxWidth: 1400, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '80px' }}>
            <Title level={2} style={{
              color: '#1e293b',
              marginBottom: '16px',
              fontSize: '2.4em',
              fontWeight: 'bold'
            }}>
              强大功能，专业体验
            </Title>
            <Paragraph style={{
              fontSize: '20px',
              color: '#475569',
              maxWidth: '800px',
              margin: '0 auto',
              lineHeight: '1.7'
            }}>
              从代码编辑到执行管理，CodeRunner 为您提供完整的远程代码执行解决方案
            </Paragraph>
          </div>

          <Row gutter={[40, 40]} justify="center">
            {/* 功能卡片组 */}
            <Col xs={24} lg={8}>
              <div style={{
                background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                borderRadius: '24px',
                padding: '40px 30px',
                height: '100%',
                boxShadow: '0 15px 40px rgba(0,0,0,0.06)',
                border: '1px solid #e2e8f0',
                position: 'relative',
                overflow: 'hidden',
                transition: 'all 0.4s ease'
              }}>
                {/* 渐变背景装饰 */}
                <div style={{
                  position: 'absolute',
                  top: '-50px',
                  right: '-50px',
                  width: '150px',
                  height: '150px',
                  background: 'radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%)',
                  borderRadius: '50%'
                }} />

                <div style={{ position: 'relative', zIndex: 1 }}>
                  <div style={{
                    width: '70px',
                    height: '70px',
                    borderRadius: '20px',
                    background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '30px',
                    boxShadow: '0 8px 25px rgba(59, 130, 246, 0.25)'
                  }}>
                    <CodeOutlined style={{ fontSize: '32px', color: 'white' }} />
                  </div>

                  <Title level={3} style={{
                    color: '#1e293b',
                    marginBottom: '20px',
                    fontSize: '1.4em',
                    fontWeight: '700'
                  }}>
                    智能代码编辑器
                  </Title>

                  <ul style={{
                    listStyle: 'none',
                    padding: 0,
                    margin: 0,
                    color: '#475569',
                    fontSize: '16px',
                    lineHeight: '1.8'
                  }}>
                    <li style={{ marginBottom: '12px', display: 'flex', alignItems: 'flex-start' }}>
                      <span style={{ color: '#10b981', marginRight: '12px', fontWeight: 'bold' }}>✓</span>
                      语法高亮和自动补全
                    </li>
                    <li style={{ marginBottom: '12px', display: 'flex', alignItems: 'flex-start' }}>
                      <span style={{ color: '#10b981', marginRight: '12px', fontWeight: 'bold' }}>✓</span>
                      多文件代码项目管理
                    </li>
                    <li style={{ marginBottom: '12px', display: 'flex', alignItems: 'flex-start' }}>
                      <span style={{ color: '#10b981', marginRight: '12px', fontWeight: 'bold' }}>✓</span>
                      实时代码错误检测
                    </li>
                    <li style={{ display: 'flex', alignItems: 'flex-start' }}>
                      <span style={{ color: '#10b981', marginRight: '12px', fontWeight: 'bold' }}>✓</span>
                      代码格式化和美化
                    </li>
                  </ul>
                </div>
              </div>
            </Col>

            <Col xs={24} lg={8}>
              <div style={{
                background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                borderRadius: '24px',
                padding: '40px 30px',
                height: '100%',
                boxShadow: '0 15px 40px rgba(0,0,0,0.06)',
                border: '1px solid #e2e8f0',
                position: 'relative',
                overflow: 'hidden',
                transition: 'all 0.4s ease'
              }}>
                {/* 渐变背景装饰 */}
                <div style={{
                  position: 'absolute',
                  top: '-50px',
                  right: '-50px',
                  width: '150px',
                  height: '150px',
                  background: 'radial-gradient(circle, rgba(16, 185, 129, 0.1) 0%, transparent 70%)',
                  borderRadius: '50%'
                }} />

                <div style={{ position: 'relative', zIndex: 1 }}>
                  <div style={{
                    width: '70px',
                    height: '70px',
                    borderRadius: '20px',
                    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '30px',
                    boxShadow: '0 8px 25px rgba(16, 185, 129, 0.25)'
                  }}>
                    <SafetyOutlined style={{ fontSize: '32px', color: 'white' }} />
                  </div>

                  <Title level={3} style={{
                    color: '#1e293b',
                    marginBottom: '20px',
                    fontSize: '1.4em',
                    fontWeight: '700'
                  }}>
                    安全执行环境
                  </Title>

                  <ul style={{
                    listStyle: 'none',
                    padding: 0,
                    margin: 0,
                    color: '#475569',
                    fontSize: '16px',
                    lineHeight: '1.8'
                  }}>
                    <li style={{ marginBottom: '12px', display: 'flex', alignItems: 'flex-start' }}>
                      <span style={{ color: '#10b981', marginRight: '12px', fontWeight: 'bold' }}>✓</span>
                      容器化沙箱隔离
                    </li>
                    <li style={{ marginBottom: '12px', display: 'flex', alignItems: 'flex-start' }}>
                      <span style={{ color: '#10b981', marginRight: '12px', fontWeight: 'bold' }}>✓</span>
                      资源使用限制
                    </li>
                    <li style={{ marginBottom: '12px', display: 'flex', alignItems: 'flex-start' }}>
                      <span style={{ color: '#10b981', marginRight: '12px', fontWeight: 'bold' }}>✓</span>
                      执行超时保护
                    </li>
                    <li style={{ display: 'flex', alignItems: 'flex-start' }}>
                      <span style={{ color: '#10b981', marginRight: '12px', fontWeight: 'bold' }}>✓</span>
                      恶意代码检测
                    </li>
                  </ul>
                </div>
              </div>
            </Col>

            <Col xs={24} lg={8}>
              <div style={{
                background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)',
                borderRadius: '24px',
                padding: '40px 30px',
                height: '100%',
                boxShadow: '0 15px 40px rgba(0,0,0,0.06)',
                border: '1px solid #e2e8f0',
                position: 'relative',
                overflow: 'hidden',
                transition: 'all 0.4s ease'
              }}>
                {/* 渐变背景装饰 */}
                <div style={{
                  position: 'absolute',
                  top: '-50px',
                  right: '-50px',
                  width: '150px',
                  height: '150px',
                  background: 'radial-gradient(circle, rgba(139, 92, 246, 0.1) 0%, transparent 70%)',
                  borderRadius: '50%'
                }} />

                <div style={{ position: 'relative', zIndex: 1 }}>
                  <div style={{
                    width: '70px',
                    height: '70px',
                    borderRadius: '20px',
                    background: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '30px',
                    boxShadow: '0 8px 25px rgba(139, 92, 246, 0.25)'
                  }}>
                    <GlobalOutlined style={{ fontSize: '32px', color: 'white' }} />
                  </div>

                  <Title level={3} style={{
                    color: '#1e293b',
                    marginBottom: '20px',
                    fontSize: '1.4em',
                    fontWeight: '700'
                  }}>
                    API 和集成
                  </Title>

                  <ul style={{
                    listStyle: 'none',
                    padding: 0,
                    margin: 0,
                    color: '#475569',
                    fontSize: '16px',
                    lineHeight: '1.8'
                  }}>
                    <li style={{ marginBottom: '12px', display: 'flex', alignItems: 'flex-start' }}>
                      <span style={{ color: '#10b981', marginRight: '12px', fontWeight: 'bold' }}>✓</span>
                      RESTful API 接口
                    </li>
                    <li style={{ marginBottom: '12px', display: 'flex', alignItems: 'flex-start' }}>
                      <span style={{ color: '#10b981', marginRight: '12px', fontWeight: 'bold' }}>✓</span>
                      Webhook 通知支持
                    </li>
                    <li style={{ marginBottom: '12px', display: 'flex', alignItems: 'flex-start' }}>
                      <span style={{ color: '#10b981', marginRight: '12px', fontWeight: 'bold' }}>✓</span>
                      第三方服务集成
                    </li>
                    <li style={{ display: 'flex', alignItems: 'flex-start' }}>
                      <span style={{ color: '#10b981', marginRight: '12px', fontWeight: 'bold' }}>✓</span>
                      详细的执行日志
                    </li>
                  </ul>
                </div>
              </div>
            </Col>
          </Row>

          {/* 统计数据展示 */}
          <div style={{
            marginTop: '80px',
            background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
            borderRadius: '24px',
            padding: '60px 40px',
            textAlign: 'center',
            boxShadow: '0 25px 60px rgba(0,0,0,0.15)'
          }}>
            <Row gutter={[40, 40]} justify="center">
              <Col xs={12} md={6}>
                <div style={{ color: 'white' }}>
                  <div style={{
                    fontSize: '3em',
                    fontWeight: 'bold',
                    marginBottom: '10px',
                    background: 'linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent'
                  }}>
                    99.9%
                  </div>
                  <div style={{ fontSize: '16px', color: '#94a3b8', fontWeight: '500' }}>
                    服务可用性
                  </div>
                </div>
              </Col>
              <Col xs={12} md={6}>
                <div style={{ color: 'white' }}>
                  <div style={{
                    fontSize: '3em',
                    fontWeight: 'bold',
                    marginBottom: '10px',
                    background: 'linear-gradient(135deg, #34d399 0%, #10b981 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent'
                  }}>
                    &lt;0.5s
                  </div>
                  <div style={{ fontSize: '16px', color: '#94a3b8', fontWeight: '500' }}>
                    平均响应时间
                  </div>
                </div>
              </Col>
              <Col xs={12} md={6}>
                <div style={{ color: 'white' }}>
                  <div style={{
                    fontSize: '3em',
                    fontWeight: 'bold',
                    marginBottom: '10px',
                    background: 'linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent'
                  }}>
                    10M+
                  </div>
                  <div style={{ fontSize: '16px', color: '#94a3b8', fontWeight: '500' }}>
                    月度执行次数
                  </div>
                </div>
              </Col>
              <Col xs={12} md={6}>
                <div style={{ color: 'white' }}>
                  <div style={{
                    fontSize: '3em',
                    fontWeight: 'bold',
                    marginBottom: '10px',
                    background: 'linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent'
                  }}>
                    24/7
                  </div>
                  <div style={{ fontSize: '16px', color: '#94a3b8', fontWeight: '500' }}>
                    技术支持
                  </div>
                </div>
              </Col>
            </Row>
          </div>
        </div>
      </div>

      {/* Examples Section */}
      <div
        id="examples"
        style={{
          padding: '80px 24px',
          background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)'
        }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '60px' }}>
            <Title level={2} style={{
              color: '#1e293b',
              marginBottom: '16px',
              fontSize: '2.2em',
              fontWeight: 'bold'
            }}>
              代码示例
            </Title>
            <Paragraph style={{
              fontSize: '18px',
              color: '#475569',
              maxWidth: '700px',
              margin: '0 auto',
              lineHeight: '1.6'
            }}>
              查看一些常见的Python代码执行示例，体验平台功能
            </Paragraph>
          </div>

          <Row gutter={[30, 30]}>
            {examples.map((example, index) => (
              <Col xs={24} md={8} key={index}>
                <Card
                  title={example.title}
                  styles={{
                    header: {
                      background: 'linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%)',
                      borderBottom: '1px solid #e2e8f0',
                      borderRadius: '16px 16px 0 0',
                      fontSize: '1.1em',
                      fontWeight: '600',
                      color: '#1e293b'
                    },
                    body: { padding: '25px' }
                  }}
                  style={{
                    height: '100%',
                    border: '1px solid #e2e8f0',
                    borderRadius: '16px',
                    boxShadow: '0 8px 30px rgba(0,0,0,0.06)',
                    background: 'linear-gradient(135deg, #ffffff 0%, #f8fafc 100%)'
                  }}
                >
                  <pre style={{
                    background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
                    color: '#f1f5f9',
                    padding: '20px',
                    borderRadius: '12px',
                    fontSize: '13px',
                    fontFamily: 'monospace',
                    maxHeight: '200px',
                    overflow: 'auto',
                    margin: '0 0 20px 0',
                    lineHeight: '1.6',
                    boxShadow: 'inset 0 2px 8px rgba(0,0,0,0.2)'
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
                        style={{
                          background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
                          border: 'none',
                          borderRadius: '20px',
                          fontWeight: '600',
                          boxShadow: '0 2px 8px rgba(24, 144, 255, 0.3)'
                        }}
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
        background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #f8fafc 100%)',
        padding: '140px 24px',
        textAlign: 'center',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* 背景装饰元素 */}
        <div style={{
          position: 'absolute',
          top: '-50px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '600px',
          height: '200px',
          background: 'radial-gradient(ellipse, rgba(24, 144, 255, 0.1) 0%, transparent 70%)',
          borderRadius: '50%'
        }} />
        <div style={{
          position: 'absolute',
          bottom: '-100px',
          right: '-100px',
          width: '300px',
          height: '300px',
          background: 'radial-gradient(circle, rgba(114, 46, 209, 0.08) 0%, transparent 70%)',
          borderRadius: '50%'
        }} />

        <div style={{ maxWidth: 700, margin: '0 auto', position: 'relative', zIndex: 1 }}>
          <Title level={2} style={{
            color: '#1e293b',
            marginBottom: '24px',
            fontSize: '3em',
            fontWeight: 'bold',
            letterSpacing: '-1px'
          }}>
            准备好开始了吗？
          </Title>
          <Paragraph style={{
            fontSize: '22px',
            color: '#475569',
            marginBottom: '50px',
            lineHeight: '1.7',
            fontWeight: '400'
          }}>
            立即注册，免费使用 CodeRunner 平台执行您的 Python 代码<br/>
            支持代码保存、API调用、执行历史记录等完整功能
          </Paragraph>
          <Button
            type="primary"
            size="large"
            icon={<RocketOutlined />}
            onClick={() => window.location.href = '/login'}
            style={{
              background: 'linear-gradient(135deg, #1890ff 0%, #722ed1 100%)',
              border: 'none',
              height: '64px',
              padding: '0 56px',
              fontSize: '20px',
              borderRadius: '32px',
              fontWeight: 'bold',
              boxShadow: '0 8px 24px rgba(24, 144, 255, 0.3)',
              transition: 'all 0.3s ease'
            }}
          >
            免费开始使用
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ProductHomePage;