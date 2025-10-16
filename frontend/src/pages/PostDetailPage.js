import React, { useState, useEffect } from 'react';
import {
  Card,
  Avatar,
  Button,
  Input,
  message,
  Spin,
  Empty,
  Space,
  Typography,
  Divider,
  Row,
  Col,
  Tag,
  Tooltip,
  Modal,
  Form,
  Select
} from 'antd';
import Comment from '../components/Comment';
import {
  HeartOutlined,
  StarOutlined,
  MessageOutlined,
  SendOutlined,
  UserOutlined,
  EyeOutlined,
  ShareAltOutlined,
  LikeOutlined,
  DownloadOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../components/AuthContext';
import moment from 'moment';
import {
  getPost,
  likePost,
  favoritePost,
  createComment,
  getComments,
  likeComment,
  saveCodeToLibraryFromShare,
  getAvailableEnvironments,
  deletePost
} from '../services/api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const PostDetailPage = () => {
  const navigate = useNavigate();
  const { postId } = useParams();
  const { user } = useAuth();
  const [post, setPost] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [commentLoading, setCommentLoading] = useState(false);
  const [submittingComment, setSubmittingComment] = useState(false);
  const [commentContent, setCommentContent] = useState('');
  const [replyingTo, setReplyingTo] = useState(null);
  const [replyContent, setReplyContent] = useState('');
  const [saveCodeModal, setSaveCodeModal] = useState(false);
  const [selectedCode, setSelectedCode] = useState(null);
  const [availableEnvs, setAvailableEnvs] = useState([]);
  const [saveCodeForm] = Form.useForm();

  // Load post details
  const loadPost = async () => {
    try {
      setLoading(true);
      const response = await getPost(postId);
      setPost(response.data);
    } catch (error) {
      message.error('加载帖子失败');
      console.error('Load post error:', error);
      navigate('/community');
    } finally {
      setLoading(false);
    }
  };

  // Load comments
  const loadComments = async () => {
    try {
      setCommentLoading(true);
      const response = await getComments(postId);
      setComments(response.data.comments || []);
    } catch (error) {
      console.error('Load comments error:', error);
    } finally {
      setCommentLoading(false);
    }
  };

  useEffect(() => {
    if (postId) {
      loadPost();
      loadComments();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [postId]);

  // Handle like post
  const handleLikePost = async () => {
    try {
      const response = await likePost(postId);
      setPost({
        ...post,
        like_count: response.data.like_count,
        is_liked_by_current_user: response.data.is_liked
      });
      message.success(response.data.message);
    } catch (error) {
      message.error('操作失败');
      console.error('Like post error:', error);
    }
  };

  // Handle favorite post
  const handleFavoritePost = async () => {
    try {
      const response = await favoritePost(postId);
      setPost({
        ...post,
        favorite_count: response.data.favorite_count,
        is_favorited_by_current_user: response.data.is_favorited
      });
      message.success(response.data.message);
    } catch (error) {
      message.error('操作失败');
      console.error('Favorite post error:', error);
    }
  };

  // Handle delete post
  const handleDeletePost = async () => {
    Modal.confirm({
      title: '确认删除帖子',
      content: '删除帖子后，相关分享的代码将设为私密状态。此操作不可恢复。',
      okText: '确认删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: async () => {
        try {
          await deletePost(postId);
          message.success('帖子删除成功');
          navigate('/community');
        } catch (error) {
          message.error('删除失败');
          console.error('Delete post error:', error);
        }
      }
    });
  };

  // Handle submit comment
  const handleSubmitComment = async () => {
    if (!commentContent.trim()) {
      message.warning('请输入评论内容');
      return;
    }

    try {
      setSubmittingComment(true);
      const response = await createComment(postId, {
        content: commentContent.trim(),
        parent_id: null
      });

      setComments([response.data, ...comments]);
      setCommentContent('');
      setPost({
        ...post,
        comment_count: post.comment_count + 1
      });
      message.success('评论发布成功');
    } catch (error) {
      message.error('评论发布失败');
      console.error('Submit comment error:', error);
    } finally {
      setSubmittingComment(false);
    }
  };

  // Handle reply to comment
  const handleReply = async (commentId) => {
    if (!replyContent.trim()) {
      message.warning('请输入回复内容');
      return;
    }

    try {
      const response = await createComment(postId, {
        content: replyContent.trim(),
        parent_id: commentId
      });

      // Update comments with new reply
      const updateComments = (comments) => {
        return comments.map(comment => {
          if (comment.id === commentId) {
            return {
              ...comment,
              replies: [response.data, ...(comment.replies || [])]
            };
          }
          if (comment.replies) {
            return {
              ...comment,
              replies: updateComments(comment.replies)
            };
          }
          return comment;
        });
      };

      setComments(updateComments(comments));
      setReplyContent('');
      setReplyingTo(null);
      setPost({
        ...post,
        comment_count: post.comment_count + 1
      });
      message.success('回复成功');
    } catch (error) {
      message.error('回复失败');
      console.error('Reply error:', error);
    }
  };

  // Handle like comment
  const handleLikeComment = async (commentId) => {
    try {
      await likeComment(commentId);
      // Update comment likes in local state
      const updateCommentLikes = (comments) => {
        return comments.map(comment => {
          if (comment.id === commentId) {
            return {
              ...comment,
              like_count: comment.is_liked_by_current_user
                ? comment.like_count - 1
                : comment.like_count + 1,
              is_liked_by_current_user: !comment.is_liked_by_current_user
            };
          }
          if (comment.replies) {
            return {
              ...comment,
              replies: updateCommentLikes(comment.replies)
            };
          }
          return comment;
        });
      };
      setComments(updateCommentLikes(comments));
    } catch (error) {
      message.error('操作失败');
      console.error('Like comment error:', error);
    }
  };

  // Simple markdown to HTML converter
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

  // Handle save shared code
  const handleSaveSharedCode = async (code) => {
    try {
      const response = await getAvailableEnvironments();
      setAvailableEnvs(response.data.environments || []);
      setSelectedCode(code);
      saveCodeForm.setFieldsValue({
        title: `[Copy] ${code.title}`,
        description: code.description,
        conda_env: 'base'
      });
      setSaveCodeModal(true);
    } catch (error) {
      console.error('Load environments error:', error);
    }
  };

  // Handle save code to library
  const handleSaveCode = async (values) => {
    try {
      const response = await saveCodeToLibraryFromShare({
        source_code_id: selectedCode.id,
        title: values.title,
        description: values.description,
        conda_env: values.conda_env
      });
      message.success(response.data.message);
      setSaveCodeModal(false);
      setSelectedCode(null);
      saveCodeForm.resetFields();
    } catch (error) {
      message.error(error.response?.data?.detail || '保存失败');
      console.error('Save code error:', error);
    }
  };

  // Render comment item
  const renderComment = (comment) => (
    <Comment
      key={comment.id}
      author={
        <Space>
          <Text strong>{comment.author_full_name || comment.author_username}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {moment(comment.created_at).fromNow()}
          </Text>
        </Space>
      }
      avatar={
        <Avatar
          src={comment.author_avatar}
          icon={<UserOutlined />}
        />
      }
      content={
        <div>
          <Paragraph style={{ marginBottom: '8px' }}>
            {comment.content}
          </Paragraph>
          <Space size="small">
            <Tooltip title={comment.is_liked_by_current_user ? "取消点赞" : "点赞"}>
              <Button
                type="text"
                size="small"
                icon={<LikeOutlined />}
                style={{
                  color: comment.is_liked_by_current_user ? '#ff4d4f' : 'inherit',
                  fontSize: '12px'
                }}
                onClick={() => handleLikeComment(comment.id)}
              >
                {comment.like_count || 0}
              </Button>
            </Tooltip>
            <Button
              type="text"
              size="small"
              icon={<MessageOutlined />}
              style={{ fontSize: '12px' }}
              onClick={() => setReplyingTo(replyingTo === comment.id ? null : comment.id)}
            >
              回复
            </Button>
          </Space>

          {/* Reply input */}
          {replyingTo === comment.id && (
            <div style={{ marginTop: '12px' }}>
              <TextArea
                rows={3}
                placeholder="写下你的回复..."
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                style={{ marginBottom: '8px' }}
              />
              <Space>
                <Button
                  type="primary"
                  size="small"
                  icon={<SendOutlined />}
                  onClick={() => handleReply(comment.id)}
                >
                  发布回复
                </Button>
                <Button
                  size="small"
                  onClick={() => {
                    setReplyingTo(null);
                    setReplyContent('');
                  }}
                >
                  取消
                </Button>
              </Space>
            </div>
          )}

          {/* Render replies */}
          {comment.replies && comment.replies.length > 0 && (
            <div style={{ marginTop: '16px', marginLeft: '48px' }}>
              {comment.replies.map(renderComment)}
            </div>
          )}
        </div>
      }
    />
  );

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!post) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Empty description="帖子不存在" />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', maxWidth: '1000px', margin: '0 auto' }}>
      {/* Back button */}
      <Button
        type="text"
        onClick={() => navigate('/community')}
        style={{ marginBottom: '16px' }}
      >
        ← 返回社区
      </Button>

      {/* Post Content */}
      <Card>
        {/* Post Header */}
        <div style={{ marginBottom: '24px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <Avatar
                size="large"
                src={post.author_avatar}
                icon={<UserOutlined />}
                style={{ marginRight: '12px' }}
              />
              <div>
                <Text strong style={{ fontSize: '16px' }}>
                  {post.author_full_name || post.author_username}
                </Text>
                <br />
                <Text type="secondary">
                  {moment(post.created_at).format('YYYY-MM-DD HH:mm')}
                </Text>
              </div>
            </div>
            <Space>
              <Tooltip title={post.is_liked_by_current_user ? "取消点赞" : "点赞"}>
                <Button
                  icon={<HeartOutlined />}
                  style={{
                    color: post.is_liked_by_current_user ? '#ff4d4f' : 'inherit'
                  }}
                  onClick={handleLikePost}
                >
                  {post.like_count}
                </Button>
              </Tooltip>
              <Tooltip title={post.is_favorited_by_current_user ? "取消收藏" : "收藏"}>
                <Button
                  icon={<StarOutlined />}
                  style={{
                    color: post.is_favorited_by_current_user ? '#faad14' : 'inherit'
                  }}
                  onClick={handleFavoritePost}
                >
                  {post.favorite_count}
                </Button>
              </Tooltip>
              {(user && (user.id === post.user_id || user.is_admin)) && (
                <Tooltip title="删除帖子">
                  <Button
                    icon={<DeleteOutlined />}
                    style={{ color: '#ff4d4f' }}
                    onClick={handleDeletePost}
                  >
                    删除
                  </Button>
                </Tooltip>
              )}
            </Space>
          </div>
        </div>

        {/* Post Title */}
        <Title level={2} style={{ marginBottom: '16px' }}>
          {post.title}
        </Title>

        {/* Post Summary */}
        {post.summary && (
          <Paragraph
            style={{
              marginBottom: '16px',
              padding: '12px',
              backgroundColor: '#f5f5f5',
              borderLeft: '4px solid #1890ff',
              borderRadius: '4px'
            }}
          >
            <Text type="secondary">摘要：{post.summary}</Text>
          </Paragraph>
        )}

        {/* Post Tags */}
        {post.tags && (
          <div style={{ marginBottom: '16px' }}>
            {post.tags.split(',').map((tag, index) => (
              <Tag key={index} color="blue" style={{ marginBottom: '4px' }}>
                {tag.trim()}
              </Tag>
            ))}
          </div>
        )}

        {/* Shared Codes */}
        {post.shared_codes && post.shared_codes.length > 0 && (
          <div style={{ marginBottom: '16px' }}>
            <Title level={5}>分享的代码：</Title>
            <Row gutter={[8, 8]}>
              {post.shared_codes.map((code) => (
                <Col key={code.id}>
                  <Card
                    size="small"
                    hoverable
                    style={{ cursor: 'pointer' }}
                  >
                    <div onClick={() => navigate(`/code-library?code=${code.id}`)}>
                      <Space>
                        <ShareAltOutlined />
                        <div>
                          <Text strong>{code.title}</Text>
                          <br />
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            {code.language || 'python'}
                          </Text>
                        </div>
                      </Space>
                    </div>
                    <div style={{ marginTop: '8px', textAlign: 'right' }}>
                      <Button
                        type="primary"
                        size="small"
                        icon={<DownloadOutlined />}
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSaveSharedCode(code);
                        }}
                      >
                        转存
                      </Button>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </div>
        )}

        <Divider />

        {/* Post Content */}
        <div
          style={{
            minHeight: '200px',
            lineHeight: '1.6',
            fontSize: '16px'
          }}
          dangerouslySetInnerHTML={{ __html: markdownToHtml(post.content) }}
        />

        {/* Post Stats */}
        <Divider />
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <Space>
            <EyeOutlined style={{ color: '#52c41a' }} />
            <Text>{post.view_count} 浏览</Text>
          </Space>
          <Space>
            <HeartOutlined style={{ color: '#ff4d4f' }} />
            <Text>{post.like_count} 点赞</Text>
          </Space>
          <Space>
            <MessageOutlined style={{ color: '#1890ff' }} />
            <Text>{post.comment_count} 评论</Text>
          </Space>
          <Space>
            <StarOutlined style={{ color: '#faad14' }} />
            <Text>{post.favorite_count} 收藏</Text>
          </Space>
        </div>
      </Card>

      {/* Comment Section */}
      <Card title="评论区" style={{ marginTop: '24px' }}>
        {/* Comment Input */}
        <div style={{ marginBottom: '24px' }}>
          <TextArea
            rows={4}
            placeholder="写下你的评论..."
            value={commentContent}
            onChange={(e) => setCommentContent(e.target.value)}
            style={{ marginBottom: '12px' }}
          />
          <div style={{ textAlign: 'right' }}>
            <Button
              type="primary"
              icon={<SendOutlined />}
              loading={submittingComment}
              onClick={handleSubmitComment}
            >
              发布评论
            </Button>
          </div>
        </div>

        {/* Comments List */}
        <Spin spinning={commentLoading}>
          {comments.length === 0 ? (
            <Empty description="暂无评论，快来发表第一条评论吧！" />
          ) : (
            <div>
              {comments.map(renderComment)}
            </div>
          )}
        </Spin>
      </Card>

      {/* Save Code Modal */}
      <Modal
        title="转存代码到我的代码库"
        open={saveCodeModal}
        onCancel={() => {
          setSaveCodeModal(false);
          setSelectedCode(null);
          saveCodeForm.resetFields();
        }}
        onOk={() => saveCodeForm.submit()}
        okText="转存"
        cancelText="取消"
      >
        <Form
          form={saveCodeForm}
          layout="vertical"
          onFinish={handleSaveCode}
        >
          <Form.Item
            name="title"
            label="代码标题"
            rules={[{ required: true, message: '请输入代码标题' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="description" label="代码描述">
            <TextArea rows={3} />
          </Form.Item>
          <Form.Item
            name="conda_env"
            label="运行环境"
            rules={[{ required: true, message: '请选择运行环境' }]}
          >
            <Select>
              {availableEnvs.map((env) => (
                <Select.Option key={env.name} value={env.name}>
                  {env.display_name} {env.is_default && '(默认)'}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PostDetailPage;