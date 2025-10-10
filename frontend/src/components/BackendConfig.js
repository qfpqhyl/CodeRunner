import { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Alert,
  Typography,
  Space,
  Tooltip,
  Badge
} from 'antd';
import {
  SettingOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  LoadingOutlined,
  SyncOutlined,
  ApiOutlined
} from '@ant-design/icons';
import { updateBackendUrl, testBackendConnection, getCurrentBackendUrl } from '../services/api';

const { Title, Text } = Typography;

const BackendConfig = ({ onConfigured }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testing, setTesting] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('unknown');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    // Initialize form with current backend URL but don't auto-test
    const currentUrl = getCurrentBackendUrl();
    form.setFieldsValue({ backendUrl: currentUrl });
    // Reset connection status to unknown
    setConnectionStatus('unknown');
    setErrorMessage('');
  }, [form]);

  const testConnection = async (url) => {
    if (!url) return;

    setTesting(true);
    setConnectionStatus('testing');
    setErrorMessage('');

    try {
      const result = await testBackendConnection(url);
      if (result.success) {
        setConnectionStatus('success');
      } else {
        setConnectionStatus('error');
        setErrorMessage(result.message);
      }
    } catch (error) {
      setConnectionStatus('error');
      setErrorMessage(error.message || '连接测试失败');
    } finally {
      setTesting(false);
    }
  };

  const handleUrlChange = (e) => {
    const url = e.target.value;
    if (url) {
      // Debounce connection test
      const timer = setTimeout(() => {
        testConnection(url);
      }, 1000);
      return () => clearTimeout(timer);
    } else {
      setConnectionStatus('unknown');
      setErrorMessage('');
    }
  };

  const handleTestConnection = async () => {
    const url = form.getFieldValue('backendUrl');
    if (url) {
      await testConnection(url);
    }
  };

  const handleSaveConfig = async (values) => {
    setLoading(true);

    try {
      await updateBackendUrl(values.backendUrl);

      // Test the connection after saving
      const result = testBackendConnection(values.backendUrl);
      if (result.success) {
        setConnectionStatus('success');
        if (onConfigured) {
          onConfigured(values.backendUrl);
        }
      } else {
        setConnectionStatus('error');
        setErrorMessage(result.message);
      }
    } catch (error) {
      setErrorMessage('配置保存失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = () => {
    switch (connectionStatus) {
      case 'testing':
        return <LoadingOutlined style={{ color: '#1890ff' }} />;
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ApiOutlined style={{ color: '#8c8c8c' }} />;
    }
  };

  const getStatusBadge = () => {
    switch (connectionStatus) {
      case 'testing':
        return <Badge status="processing" text="测试中..." />;
      case 'success':
        return <Badge status="success" text="已连接" />;
      case 'error':
        return <Badge status="error" text="连接失败" />;
      default:
        return <Badge status="default" text="未测试" />;
    }
  };

  return (
    <div style={{ padding: '24px', height: '100%', overflow: 'auto' }}>
      <Title level={4} style={{ marginBottom: 24, color: '#1e293b' }}>
        <SettingOutlined style={{ marginRight: 8, color: '#1890ff' }} />
        后端服务配置
      </Title>

      <Card
        style={{ marginBottom: 20 }}
        styles={{ body: { padding: 20 } }}
      >
        <div style={{ marginBottom: 20 }}>
          <Space align="center" style={{ marginBottom: 16 }}>
            {getStatusIcon()}
            <div>
              <Text strong style={{ fontSize: '16px', color: '#1e293b' }}>
                后端连接状态
              </Text>
              <div style={{ marginTop: 4 }}>
                {getStatusBadge()}
              </div>
            </div>
          </Space>

          {errorMessage && (
            <Alert
              message={errorMessage}
              type="error"
              showIcon
              style={{ marginTop: 16 }}
              action={
                <Button size="small" onClick={handleTestConnection}>
                  <SyncOutlined /> 重试
                </Button>
              }
            />
          )}
        </div>

        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveConfig}
        >
          <Form.Item
            label={
              <Space>
                <Text strong>后端 API 地址</Text>
                <Tooltip title="CodeRunner 后端服务的访问地址，通常为 http://localhost:8000 或 http://your-server-ip:8000">
                  <ExclamationCircleOutlined style={{ color: '#8c8c8c' }} />
                </Tooltip>
              </Space>
            }
            name="backendUrl"
            rules={[
              { required: true, message: '请输入后端 API 地址' },
              {
                type: 'url',
                message: '请输入有效的 URL 地址'
              }
            ]}
          >
            <Input
              placeholder="http://localhost:8000"
              size="large"
              prefix={<ApiOutlined style={{ color: '#1890ff' }} />}
              onChange={handleUrlChange}
              style={{
                borderRadius: 8,
                fontSize: '14px'
              }}
              suffix={
                testing ? (
                  <LoadingOutlined />
                ) : (
                  <Button
                    type="text"
                    size="small"
                    onClick={handleTestConnection}
                    disabled={!form.getFieldValue('backendUrl')}
                  >
                    测试
                  </Button>
                )
              }
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              disabled={connectionStatus !== 'success'}
              size="large"
              block
              style={{
                height: '44px',
                borderRadius: 8,
                fontSize: '16px',
                fontWeight: 500
              }}
            >
              {connectionStatus === 'success' ? '保存配置' : '请先测试连接'}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default BackendConfig;