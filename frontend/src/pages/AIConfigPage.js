import React, { useState, useEffect } from 'react';
import { Card, Button, Table, Space, Modal, Form, Input, Switch, message, Popconfirm, Typography, Tag, Tooltip, Alert } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, RobotOutlined, SettingOutlined, CheckCircleOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import { createAIConfig, getAIConfigs, updateAIConfig, deleteAIConfig } from '../services/api';
import { useAuth } from '../components/AuthContext';

const { Title, Paragraph, Text } = Typography;

const AIConfigPage = () => {
  // eslint-disable-next-line no-empty-pattern
  const { } = useAuth();
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [form] = Form.useForm();

  // Load AI configurations
  const loadConfigs = async () => {
    setLoading(true);
    try {
      const response = await getAIConfigs();
      setConfigs(response.data);
    } catch (err) {
      message.error('加载AI配置失败');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConfigs();
  }, []);

  // Handle form submission
  const handleSubmit = async (values) => {
    try {
      if (editingConfig) {
        await updateAIConfig(editingConfig.id, values);
        message.success('AI配置更新成功！');
      } else {
        await createAIConfig(values);
        message.success('AI配置创建成功！');
      }

      setModalVisible(false);
      setEditingConfig(null);
      form.resetFields();
      loadConfigs();
    } catch (err) {
      message.error(err.response?.data?.detail || '操作失败');
    }
  };

  // Handle edit
  const handleEdit = (config) => {
    setEditingConfig(config);
    form.setFieldsValue({
      config_name: config.config_name,
      provider: config.provider,
      model_name: config.model_name,
      api_key: config.api_key,
      base_url: config.base_url,
      is_active: config.is_active
    });
    setModalVisible(true);
  };

  // Handle delete
  const handleDelete = async (configId) => {
    try {
      await deleteAIConfig(configId);
      message.success('AI配置删除成功！');
      loadConfigs();
    } catch (err) {
      message.error(err.response?.data?.detail || '删除失败');
    }
  };

  // Handle toggle active status
  const handleToggleActive = async (config) => {
    try {
      await updateAIConfig(config.id, { ...config, is_active: !config.is_active });
      message.success(`AI配置已${!config.is_active ? '启用' : '禁用'}！`);
      loadConfigs();
    } catch (err) {
      message.error(err.response?.data?.detail || '操作失败');
    }
  };

  // Table columns
  const columns = [
    {
      title: '配置名称',
      dataIndex: 'config_name',
      key: 'config_name',
      render: (text, record) => (
        <Space>
          <RobotOutlined style={{ color: '#722ed1' }} />
          <span style={{ fontWeight: 500 }}>{text}</span>
          {record.is_active && (
            <Tag color="success" size="small" icon={<CheckCircleOutlined />}>
              活跃
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: '提供商',
      dataIndex: 'provider',
      key: 'provider',
      render: (text) => (
        <Tag color="blue">{text}</Tag>
      ),
    },
    {
      title: '模型名称',
      dataIndex: 'model_name',
      key: 'model_name',
      render: (text) => (
        <Text code>{text}</Text>
      ),
    },
    {
      title: 'API密钥',
      dataIndex: 'api_key',
      key: 'api_key',
      render: (key) => (
        <Text code style={{ fontFamily: 'monospace', fontSize: '12px' }}>
          {key.substring(0, 8)}***{key.substring(key.length - 4)}
        </Text>
      ),
    },
    {
      title: '状态',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive, record) => (
        <Switch
          checked={isActive}
          onChange={() => handleToggleActive(record)}
          checkedChildren="启用"
          unCheckedChildren="禁用"
          size="small"
        />
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleString(),
    },
    {
      title: '操作',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Tooltip title="编辑配置">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
              size="small"
            />
          </Tooltip>
          <Popconfirm
            title="确定要删除这个AI配置吗？"
            description="删除后将无法恢复，请谨慎操作。"
            onConfirm={() => handleDelete(record.id)}
            okText="确定"
            cancelText="取消"
            okType="danger"
          >
            <Tooltip title="删除配置">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                size="small"
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: 24 }}>
          <Title level={2}>
            <RobotOutlined style={{ marginRight: 8, color: '#722ed1' }} />
            AI 模型配置
          </Title>
          <Paragraph type="secondary">
            配置您的AI模型API，用于代码生成功能。支持多种AI提供商，如通义千问、OpenAI等。
          </Paragraph>
        </div>

        {configs.length === 0 && !loading && (
          <Alert
            message="暂无AI配置"
            description="请添加您的第一个AI模型配置以使用AI代码生成功能。"
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
            icon={<ExclamationCircleOutlined />}
          />
        )}

        <div style={{ marginBottom: 16 }}>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingConfig(null);
              form.resetFields();
              form.setFieldsValue({
                provider: 'qwen',
                model_name: 'qwen-plus',
                base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                is_active: true
              });
              setModalVisible(true);
            }}
            style={{ background: 'linear-gradient(135deg, #722ed1 0%, #531dab 100%)', border: 'none' }}
          >
            添加AI配置
          </Button>
        </div>

        <Table
          columns={columns}
          dataSource={configs}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个配置`,
          }}
          locale={{
            emptyText: '暂无AI配置，点击上方按钮添加第一个配置'
          }}
        />
      </Card>

      {/* Add/Edit Modal */}
      <Modal
        title={
          <Space>
            <SettingOutlined style={{ color: '#722ed1' }} />
            {editingConfig ? '编辑AI配置' : '添加AI配置'}
          </Space>
        }
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingConfig(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="config_name"
            label="配置名称"
            rules={[
              { required: true, message: '请输入配置名称' },
              { min: 2, message: '配置名称至少2个字符' }
            ]}
          >
            <Input placeholder="给这个AI配置起个名字，如：通义千问主要配置" />
          </Form.Item>

          <Form.Item
            name="provider"
            label="AI提供商"
            rules={[{ required: true, message: '请选择AI提供商' }]}
          >
            <Input placeholder="如：qwen, openai, anthropic" />
          </Form.Item>

          <Form.Item
            name="model_name"
            label="模型名称"
            rules={[{ required: true, message: '请输入模型名称' }]}
          >
            <Input placeholder="如：qwen-plus, gpt-4, claude-3-sonnet" />
          </Form.Item>

          <Form.Item
            name="api_key"
            label="API密钥"
            rules={[
              { required: true, message: '请输入API密钥' },
              { min: 10, message: 'API密钥长度不正确' }
            ]}
          >
            <Input.Password placeholder="输入您的AI API密钥" />
          </Form.Item>

          <Form.Item
            name="base_url"
            label="API基础URL"
            rules={[{ required: true, message: '请输入API基础URL' }]}
          >
            <Input placeholder="如：https://dashscope.aliyuncs.com/compatible-mode/v1" />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="启用状态"
            valuePropName="checked"
          >
            <Switch checkedChildren="启用" unCheckedChildren="禁用" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button
                onClick={() => {
                  setModalVisible(false);
                  setEditingConfig(null);
                  form.resetFields();
                }}
              >
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {editingConfig ? '更新配置' : '添加配置'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AIConfigPage;