import React, { useState } from 'react';
import { Card, Button, Input, Typography, Space, Alert, Spin, Row, Col, Statistic, Modal, Form, message, Collapse, Select, Slider } from 'antd';
import { PlayCircleOutlined, CodeOutlined, ClockCircleOutlined, CheckCircleOutlined, UserOutlined, SaveOutlined, RobotOutlined, ThunderboltOutlined, SettingOutlined, GithubOutlined } from '@ant-design/icons';
import { executeCode, getExecutions, getUserStats, saveCodeToLibrary, generateCodeByAI, getAIConfigs, getCondaEnvironments } from '../services/api';
import { useAuth } from '../components/AuthContext';

const { Title, Paragraph } = Typography;
const { TextArea } = Input;
const { Panel } = Collapse;
const { Option } = Select;

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
  const [saveModalVisible, setSaveModalVisible] = useState(false);
  const [saveForm] = Form.useForm();

  // Conda environment states
  const [condaEnvs, setCondaEnvs] = useState(['base']); // Default to base only
  const [selectedCondaEnv, setSelectedCondaEnv] = useState('base');
  const [loadingEnvs, setLoadingEnvs] = useState(false);

  // AI-related states
  const [aiConfigs, setAIConfigs] = useState([]);
  const [selectedAIConfig, setSelectedAIConfig] = useState(null);
  const [aiPrompt, setAIPrompt] = useState('');
  const [aiGenerating, setAiGenerating] = useState(false);
  const [aiGeneratedCode, setAiGeneratedCode] = useState('');
  const [aiMaxTokens, setAiMaxTokens] = useState(2000);
  const [aiTemperature, setAiTemperature] = useState(0.7);

  const handleExecute = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await executeCode({
        code,
        conda_env: selectedCondaEnv
      });
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

  const handleSaveCode = () => {
    setSaveModalVisible(true);
  };

  const handleSaveCodeSubmit = async (values) => {
    try {
      await saveCodeToLibrary({
        title: values.title,
        description: values.description,
        code: code,
        language: 'python',
        tags: values.tags,
        conda_env: selectedCondaEnv
      });

      message.success('代码已保存到代码库！');
      setSaveModalVisible(false);
      saveForm.resetFields();
    } catch (err) {
      message.error(err.response?.data?.detail || '保存失败');
    }
  };

  // Load conda environments
  const loadCondaEnvironments = React.useCallback(async () => {
    const controller = new AbortController();

    setLoadingEnvs(true);
    try {
      const response = await getCondaEnvironments();
      if (!controller.signal.aborted) {
        setCondaEnvs(response.data);
      }
    } catch (error) {
      if (!controller.signal.aborted) {
        console.error('Failed to load conda environments:', error);
        // Fallback to base environment if loading fails
        setCondaEnvs(['base']);
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoadingEnvs(false);
      }
    }

    return () => {
      controller.abort();
    };
  }, []); // Remove loadingEnvs dependency to prevent infinite loop

  // Load AI configurations
  const loadAIConfigs = async () => {
    try {
      const response = await getAIConfigs();
      setAIConfigs(response.data);
      // Set the active config as default
      const activeConfig = response.data.find(config => config.is_active);
      if (activeConfig) {
        setSelectedAIConfig(activeConfig.id);
      }
    } catch (err) {
      console.error('Failed to load AI configs:', err);
    }
  };

  // Generate code using AI
  const handleAIGenerateCode = async () => {
    if (!aiPrompt.trim()) {
      message.error('请输入代码生成需求描述');
      return;
    }

    if (!selectedAIConfig) {
      message.error('请先选择AI配置');
      return;
    }

    setAiGenerating(true);
    try {
      const response = await generateCodeByAI({
        prompt: aiPrompt,
        config_id: selectedAIConfig,
        max_tokens: aiMaxTokens,
        temperature: aiTemperature
      });

      setAiGeneratedCode(response.data.generated_code);
      message.success('代码生成成功！');
    } catch (err) {
      message.error(err.response?.data?.detail || 'AI代码生成失败');
    } finally {
      setAiGenerating(false);
    }
  };

  // Apply AI-generated code to editor
  const handleApplyAICode = () => {
    if (aiGeneratedCode.trim()) {
      setCode(aiGeneratedCode);
      message.success('AI生成的代码已应用到编辑器');
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

    // Load AI configurations
    loadAIConfigs();

    // Load conda environments
    loadCondaEnvironments();
  }, [loadCondaEnvironments]);

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px' }}>
      <Row gutter={[24, 24]}>
        <Col span={24}>
          <Card>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Title level={2} style={{ margin: 0 }}>
                <CodeOutlined /> CodeRunner
              </Title>
              <Button
                type="default"
                icon={<GithubOutlined />}
                href="https://github.com/qfpqhyl/CodeRunner"
                target="_blank"
                rel="noopener noreferrer"
                size="large"
              >
                GitHub
              </Button>
            </div>
            <Paragraph style={{ marginTop: 16 }}>
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

            {/* AI Code Generation Panel */}
            <Collapse
              ghost
              style={{ marginBottom: 16 }}
            >
              <Panel
                header={
                  <Space>
                    <RobotOutlined style={{ color: '#722ed1' }} />
                    <span>AI 代码生成助手</span>
                    {aiConfigs.length === 0 && (
                      <span style={{ color: '#ff4d4f', fontSize: '12px' }}>(请先配置AI模型)</span>
                    )}
                  </Space>
                }
                key="ai"
              >
                {aiConfigs.length > 0 ? (
                  <div style={{ padding: '12px 0' }}>
                    <Space direction="vertical" style={{ width: '100%' }} size="middle">
                      {/* AI Configuration Selection */}
                      <div>
                        <label style={{ marginBottom: 8, display: 'block', fontSize: '14px', fontWeight: 500 }}>
                          <SettingOutlined /> AI模型配置:
                        </label>
                        <Select
                          value={selectedAIConfig}
                          onChange={setSelectedAIConfig}
                          style={{ width: '100%' }}
                          placeholder="选择AI模型配置"
                        >
                          {aiConfigs.map(config => (
                            <Option key={config.id} value={config.id}>
                              {config.config_name} ({config.provider} - {config.model_name})
                            </Option>
                          ))}
                        </Select>
                      </div>

                      {/* Prompt Input */}
                      <div>
                        <label style={{ marginBottom: 8, display: 'block', fontSize: '14px', fontWeight: 500 }}>
                          <ThunderboltOutlined /> 代码需求描述:
                        </label>
                        <TextArea
                          value={aiPrompt}
                          onChange={(e) => setAIPrompt(e.target.value)}
                          placeholder="描述您想要生成的代码功能，例如：创建一个计算斐波那契数列的函数"
                          rows={3}
                          style={{ fontSize: '14px' }}
                        />
                      </div>

                      {/* Advanced Settings */}
                      <div>
                        <Space direction="vertical" style={{ width: '100%' }} size="small">
                          <div>
                            <label style={{ fontSize: '13px', fontWeight: 500 }}>
                              最大令牌数: {aiMaxTokens}
                            </label>
                            <Slider
                              min={100}
                              max={4000}
                              value={aiMaxTokens}
                              onChange={setAiMaxTokens}
                              style={{ marginTop: 4 }}
                            />
                          </div>
                          <div>
                            <label style={{ fontSize: '13px', fontWeight: 500 }}>
                              创造性 (Temperature): {aiTemperature}
                            </label>
                            <Slider
                              min={0.1}
                              max={2.0}
                              step={0.1}
                              value={aiTemperature}
                              onChange={setAiTemperature}
                              style={{ marginTop: 4 }}
                            />
                          </div>
                        </Space>
                      </div>

                      {/* Action Buttons */}
                      <Space>
                        <Button
                          type="primary"
                          icon={<ThunderboltOutlined />}
                          onClick={handleAIGenerateCode}
                          loading={aiGenerating}
                          disabled={!selectedAIConfig || !aiPrompt.trim()}
                          style={{ background: 'linear-gradient(135deg, #722ed1 0%, #531dab 100%)', border: 'none' }}
                        >
                          {aiGenerating ? '生成中...' : '生成代码'}
                        </Button>
                        {aiGeneratedCode && (
                          <Button
                            icon={<CodeOutlined />}
                            onClick={handleApplyAICode}
                          >
                            应用到编辑器
                          </Button>
                        )}
                      </Space>

                      {/* Generated Code Preview */}
                      {aiGeneratedCode && (
                        <div>
                          <label style={{ marginBottom: 8, display: 'block', fontSize: '14px', fontWeight: 500 }}>
                            生成的代码预览:
                          </label>
                          <pre style={{
                            background: '#f6f8ff',
                            border: '1px solid #d6e4ff',
                            borderRadius: '6px',
                            padding: '12px',
                            fontSize: '12px',
                            maxHeight: '200px',
                            overflow: 'auto',
                            margin: 0
                          }}>
                            {aiGeneratedCode}
                          </pre>
                        </div>
                      )}
                    </Space>
                  </div>
                ) : (
                  <div style={{ textAlign: 'center', padding: '20px', color: '#666' }}>
                    <RobotOutlined style={{ fontSize: '24px', marginBottom: '8px' }} />
                    <div>暂无AI模型配置</div>
                    <div style={{ fontSize: '12px', marginTop: '4px' }}>
                      请先在AI配置页面添加模型配置
                    </div>
                  </div>
                )}
              </Panel>
            </Collapse>

            {/* Conda Environment Selector */}
            <div style={{ marginBottom: 16, padding: 12, background: '#f0f9ff', borderRadius: 6, border: '1px solid #d6e4ff' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center' }}>
                  <span style={{ fontWeight: 500, fontSize: '14px', color: '#1890ff' }}>
                    <SettingOutlined /> 运行环境:
                  </span>
                  <Select
                    value={selectedCondaEnv}
                    onChange={setSelectedCondaEnv}
                    style={{ width: 200, marginLeft: 12 }}
                    loading={loadingEnvs}
                    options={condaEnvs.map(env => ({
                      label: env === 'base' ? `${env} (默认)` : env,
                      value: env
                    }))}
                  />
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  选择代码执行的conda环境
                </div>
              </div>
            </div>

            <TextArea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Enter your Python code here..."
              rows={12}
              className="code-editor"
              style={{ fontSize: '14px' }}
            />
            <Space style={{ marginTop: 16 }}>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={handleExecute}
                loading={loading}
                disabled={userStats?.remaining_executions === 0}
                size="large"
              >
                Execute Code
              </Button>
              <Button
                icon={<SaveOutlined />}
                onClick={handleSaveCode}
                size="large"
              >
                保存代码
              </Button>
            </Space>
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

      {/* Save Code Modal */}
      <Modal
        title="保存代码到代码库"
        open={saveModalVisible}
        onCancel={() => setSaveModalVisible(false)}
        footer={null}
        width={600}
      >
        <Form
          form={saveForm}
          layout="vertical"
          onFinish={handleSaveCodeSubmit}
        >
          <Form.Item
            name="title"
            label="代码标题"
            rules={[{ required: true, message: '请输入代码标题' }]}
          >
            <Input placeholder="给你的代码起个名字..." />
          </Form.Item>

          <Form.Item
            name="description"
            label="代码描述"
          >
            <TextArea
              placeholder="简单描述这段代码的功能..."
              rows={3}
            />
          </Form.Item>

          <Form.Item
            name="tags"
            label="标签"
          >
            <Input placeholder="用逗号分隔多个标签，如：算法,排序,Python" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setSaveModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                保存
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default HomePage;