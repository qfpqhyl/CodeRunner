import React, { useState } from 'react';
import { Card, Button, Input, Typography, Space, Alert, Spin, Row, Col, Statistic } from 'antd';
import { PlayCircleOutlined, CodeOutlined, ClockCircleOutlined, CheckCircleOutlined, UserOutlined } from '@ant-design/icons';
import { executeCode, getExecutions, getUserStats } from '../services/api';
import { useAuth } from '../components/AuthContext';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;

const HomePage = () => {
  const { user } = useAuth();

    const [code, setCode] = useState(`# Welcome to CodeRunner\n# Write your Python code here and execute it remotely\n# User Level: ${user?.username || 'Guest'} (Level ${user?.user_level || 1})\n\nprint("Hello, World!")\nprint("Current user:", "${user?.username || 'Anonymous'}")\nprint("User level:", ${user?.user_level || 1})\n\n# Try some calculations\nx = 10\ny = 20\nresult = x + y\nprint(f"{x} + {y} = {result}")`);

  // Load example code from URL parameter if present
  React.useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const exampleCode = urlParams.get('example');
    if (exampleCode) {
      setCode(decodeURIComponent(exampleCode));
      // Clear the URL parameter
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [executions, setExecutions] = useState([]);
  const [userStats, setUserStats] = useState(null);

  const handleExecute = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await executeCode({ code });
      setResult(response.data);

      // Refresh executions list
      const execResponse = await getExecutions();
      setExecutions(execResponse.data.slice(0, 5)); // Show last 5 executions

      // Refresh user stats to update execution count
      const statsResponse = await getUserStats();
      setUserStats(statsResponse.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Execution failed');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    // Load user stats and recent executions
    getUserStats().then(response => {
      setUserStats(response.data);
    }).catch(() => {});

    getExecutions().then(response => {
      setExecutions(response.data.slice(0, 5));
    }).catch(() => {});
  }, []);

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px' }}>
      <Row gutter={[24, 24]}>
        <Col span={24}>
          <Card>
            <Title level={2}>
              <CodeOutlined /> CodeRunner
            </Title>
            <Paragraph>
              远端Python代码执行平台 - Execute Python code remotely in a secure environment
            </Paragraph>
            <Space size="large">
              <Statistic
                title="欢迎"
                value={user?.full_name || user?.username || 'Guest'}
                prefix={<CheckCircleOutlined />}
              />
              <Statistic
                title="用户等级"
                value={userStats?.level_config?.name || `等级 ${user?.user_level || 1}`}
                prefix={<UserOutlined />}
                valueStyle={{ color: userStats?.level_config?.color || '#666' }}
              />
              {userStats?.remaining_executions !== null && userStats?.remaining_executions !== undefined && (
                <Statistic
                  title="今日剩余次数"
                  value={userStats.remaining_executions}
                  suffix={`/ ${userStats.level_config?.daily_executions === -1 ? '无限制' : userStats.level_config?.daily_executions}`}
                  prefix={<ClockCircleOutlined />}
                  valueStyle={{ color: userStats.remaining_executions > 0 ? '#52c41a' : '#ff4d4f' }}
                />
              )}
              <Statistic
                title="执行时长限制"
                value={userStats?.level_config?.max_execution_time || 30}
                suffix="秒"
                prefix={<CodeOutlined />}
              />
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="Python Code Editor" size="small">
            {userStats && userStats.level_config && (
              <div style={{ marginBottom: 12, padding: 8, background: '#f0f9ff', borderRadius: 4, fontSize: '12px' }}>
                <Space split={<span>•</span>}>
                  <span style={{ color: userStats.level_config.color }}>
                    {userStats.level_config.name}
                  </span>
                  <span>时长限制: {userStats.level_config.max_execution_time}秒</span>
                  <span>内存限制: {userStats.level_config.max_memory}MB</span>
                  {userStats.level_config.daily_executions > 0 && (
                    <span style={{ color: userStats.remaining_executions > 0 ? '#52c41a' : '#ff4d4f' }}>
                      今日剩余: {userStats.remaining_executions}/{userStats.level_config.daily_executions}
                    </span>
                  )}
                  {userStats.level_config.daily_executions === -1 && (
                    <span style={{ color: '#52c41a' }}>无执行次数限制</span>
                  )}
                </Space>
              </div>
            )}
            <TextArea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Enter your Python code here..."
              rows={12}
              className="code-editor"
              style={{ fontSize: '14px' }}
            />
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              onClick={handleExecute}
              loading={loading}
              disabled={userStats?.remaining_executions === 0}
              style={{ marginTop: 16 }}
              size="large"
            >
              Execute Code
            </Button>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title="Execution Result" size="small">
            {loading && (
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Spin size="large" />
                <div style={{ marginTop: 16 }}>Executing your code...</div>
              </div>
            )}

            {error && (
              <Alert
                message="Execution Error"
                description={error}
                type="error"
                showIcon
                style={{ marginBottom: 16 }}
              />
            )}

            {result && !loading && (
              <div>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <strong>Status:</strong>
                    <span style={{
                      color: result.status === 'success' ? '#52c41a' : '#ff4d4f',
                      marginLeft: 8
                    }}>
                      {result.status.toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <strong>Execution Time:</strong>
                    <span style={{ marginLeft: 8 }}>{result.execution_time}ms</span>
                  </div>
                  <div>
                    <strong>Output:</strong>
                    <pre className="code-output" style={{
                      background: '#f5f5f5',
                      padding: '12px',
                      borderRadius: '4px',
                      marginTop: '8px',
                      maxHeight: '300px',
                      overflow: 'auto',
                      fontSize: '13px'
                    }}>
                      {result.result}
                    </pre>
                  </div>
                </Space>
              </div>
            )}

            {!loading && !result && !error && (
              <div style={{
                textAlign: 'center',
                color: '#999',
                padding: '40px 0'
              }}>
                Write some code and click "Execute Code" to see results
              </div>
            )}
          </Card>
        </Col>

        {executions.length > 0 && (
          <Col span={24}>
            <Card title="Recent Executions" size="small">
              <div style={{ maxHeight: '300px', overflow: 'auto' }}>
                {executions.map((execution) => (
                  <div key={execution.id} style={{
                    borderBottom: '1px solid #f0f0f0',
                    padding: '12px 0',
                    fontSize: '12px'
                  }}>
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      marginBottom: '8px'
                    }}>
                      <span style={{
                        color: execution.status === 'success' ? '#52c41a' : '#ff4d4f',
                        fontWeight: 'bold'
                      }}>
                        {execution.status.toUpperCase()}
                      </span>
                      <span style={{ color: '#666' }}>
                        {execution.execution_time}ms • {new Date(execution.created_at).toLocaleString()}
                      </span>
                    </div>
                    <pre className="code-output" style={{
                      background: '#fafafa',
                      padding: '8px',
                      borderRadius: '4px',
                      margin: 0,
                      maxHeight: '100px',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      {execution.result}
                    </pre>
                  </div>
                ))}
              </div>
            </Card>
          </Col>
        )}
      </Row>
    </div>
  );
};

export default HomePage;