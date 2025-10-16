import React, { useState, useEffect } from 'react';
import {
  Form,
  Input,
  Button,
  message,
  Tag,
  Switch,
  Space,
  Typography,
  Row,
  Col,
  Checkbox,
  Empty,
  Modal
} from 'antd';
import {
  SendOutlined,
  EyeOutlined,
  CodeOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { createPost, getCodeLibrary } from '../services/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

const CreatePostPage = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewContent, setPreviewContent] = useState('');
  const [userCodeLibrary, setUserCodeLibrary] = useState([]);
  const [selectedCodes, setSelectedCodes] = useState([]);

  // Load user's code library
  const loadUserCodeLibrary = async () => {
    try {
      const response = await getCodeLibrary();
      setUserCodeLibrary(response.data);
    } catch (error) {
      console.error('Load code library error:', error);
    }
  };

  useEffect(() => {
    loadUserCodeLibrary();
  }, []);

  // Handle form submission
  const handleSubmit = async (values) => {
    try {
      setLoading(true);
      const postData = {
        ...values,
        shared_code_ids: selectedCodes
      };

      await createPost(postData);
      message.success('帖子发布成功！');
      navigate('/community');
    } catch (error) {
      message.error(error.response?.data?.detail || '发布失败');
    } finally {
      setLoading(false);
    }
  };

  // Handle code selection
  const handleCodeSelect = (codeId) => {
    setSelectedCodes(prev =>
      prev.includes(codeId)
        ? prev.filter(id => id !== codeId)
        : [...prev, codeId]
    );
  };

  // Preview content
  const handlePreview = () => {
    const content = form.getFieldValue('content') || '';
    setPreviewContent(content);
    setPreviewVisible(true);
  };

  // Simple markdown to HTML converter (basic implementation)
  const markdownToHtml = (text) => {
    return text
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/\n\n/g, '</p><p>')
      .replace(/^/, '<p>')
      .replace(/$/, '</p>');
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1000px', margin: '0 auto' }}>
      <Title level={2}>发布帖子</Title>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          is_public: true
        }}
      >
        {/* Title */}
        <Form.Item
          name="title"
          label="标题"
          rules={[
            { required: true, message: '请输入帖子标题' },
            { max: 100, message: '标题不能超过100个字符' }
          ]}
        >
          <Input placeholder="请输入帖子标题" />
        </Form.Item>

        {/* Summary */}
        <Form.Item
          name="summary"
          label="摘要（可选）"
          rules={[
            { max: 200, message: '摘要不能超过200个字符' }
          ]}
        >
          <TextArea
            rows={2}
            placeholder="请输入帖子摘要，将在帖子列表中显示"
            maxLength={200}
            showCount
          />
        </Form.Item>

        {/* Content */}
        <Form.Item
          name="content"
          label="内容"
          rules={[
            { required: true, message: '请输入帖子内容' },
            { min: 10, message: '内容不能少于10个字符' }
          ]}
        >
          <TextArea
            rows={12}
            placeholder="请输入帖子内容，支持Markdown格式"
            style={{ fontFamily: 'Monaco, Consolas, monospace' }}
          />
        </Form.Item>

        <div style={{ marginBottom: '16px', display: 'flex', gap: '8px' }}>
          <Button icon={<EyeOutlined />} onClick={handlePreview}>
            预览
          </Button>
          <Text type="secondary">支持 Markdown 格式</Text>
        </div>

        {/* Tags */}
        <Form.Item
          name="tags"
          label="标签（可选）"
        >
          <Input placeholder="请输入标签，多个标签用逗号分隔" />
        </Form.Item>

        {/* Public/Private */}
        <Form.Item
          name="is_public"
          label="公开设置"
          valuePropName="checked"
        >
          <Switch checkedChildren="公开" unCheckedChildren="私密" />
        </Form.Item>

        {/* Share Code Library */}
        <Form.Item label="分享代码库（可选）">
          <Text type="secondary" style={{ marginBottom: '12px', display: 'block' }}>
            选择要分享的代码库，其他人可以查看和复制这些代码
          </Text>
          {userCodeLibrary.length > 0 ? (
            <div>
              {userCodeLibrary.map((code) => (
                <div
                  key={code.id}
                  style={{
                    padding: '8px',
                    border: '1px solid #d9d9d9',
                    borderRadius: '6px',
                    marginBottom: '8px',
                    backgroundColor: selectedCodes.includes(code.id) ? '#f6ffed' : '#fff'
                  }}
                >
                  <Row align="middle" justify="space-between">
                    <Col flex="auto">
                      <Checkbox
                        checked={selectedCodes.includes(code.id)}
                        onChange={() => handleCodeSelect(code.id)}
                      >
                        <div>
                          <Text strong>{code.title}</Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            {code.description || '无描述'}
                          </Text>
                          {code.tags && (
                            <div style={{ marginTop: '4px' }}>
                              {code.tags.split(',').map((tag, index) => (
                                <Tag key={index} size="small" style={{ marginRight: '4px' }}>
                                  {tag.trim()}
                                </Tag>
                              ))}
                            </div>
                          )}
                        </div>
                      </Checkbox>
                    </Col>
                    <Col>
                      <Text type="secondary">
                        <CodeOutlined style={{ marginRight: '4px' }} />
                        {code.language || 'python'}
                      </Text>
                    </Col>
                  </Row>
                </div>
              ))}
            </div>
          ) : (
            <Empty
              description="暂无代码库，请先在代码库中添加代码"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            />
          )}
        </Form.Item>

        {/* Form Actions */}
        <Form.Item style={{ textAlign: 'right' }}>
          <Space>
            <Button onClick={() => navigate('/community')}>
              取消
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<SendOutlined />}
            >
              发布帖子
            </Button>
          </Space>
        </Form.Item>
      </Form>

      {/* Preview Modal */}
      <Modal
        title="预览"
        open={previewVisible}
        onCancel={() => setPreviewVisible(false)}
        footer={[
          <Button key="close" onClick={() => setPreviewVisible(false)}>
            关闭
          </Button>
        ]}
        width={800}
      >
        <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
          <div dangerouslySetInnerHTML={{ __html: markdownToHtml(previewContent) }} />
        </div>
      </Modal>
    </div>
  );
};

export default CreatePostPage;