import { useState } from 'react';
import {
  Typography,
  Alert,
  Button,
  Tabs,
  Space,
  Divider,
  Tag
} from 'antd';
import {
  CheckCircleOutlined,
  CopyOutlined,
  RocketOutlined,
  GlobalOutlined,
  ThunderboltOutlined
} from '@ant-design/icons';

const { Title, Paragraph, Text } = Typography;

const DeploymentTutorial = () => {
  const [copiedCommand, setCopiedCommand] = useState('');

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopiedCommand(text);
    setTimeout(() => setCopiedCommand(''), 2000);
  };

  const CommandBlock = ({ command, description }) => (
    <div style={{ marginBottom: 16 }}>
      <Text strong style={{ color: '#374151', display: 'block', marginBottom: 8 }}>
        {description}
      </Text>
      <div style={{
        background: '#1e293b',
        borderRadius: 8,
        padding: '12px 16px',
        fontFamily: 'Monaco, Consolas, monospace',
        fontSize: '14px',
        color: '#e2e8f0',
        position: 'relative',
        border: '1px solid #334155',
        overflow: 'hidden',
        whiteSpace: 'nowrap',
        textOverflow: 'ellipsis'
      }}>
        <code style={{ textOverflow: 'ellipsis', overflow: 'hidden' }}>{command}</code>
        <Button
          type="text"
          size="small"
          icon={<CopyOutlined />}
          onClick={() => copyToClipboard(command)}
          style={{
            position: 'absolute',
            right: 8,
            top: 8,
            color: copiedCommand === command ? '#52c41a' : '#94a3b8'
          }}
        />
      </div>
      {copiedCommand === command && (
        <Alert
          message="命令已复制到剪贴板"
          type="success"
          showIcon
          size="small"
          style={{ marginTop: 8 }}
        />
      )}
    </div>
  );

  return (
    <div style={{ padding: '24px', height: '100%', overflow: 'auto' }}>
      <Title level={4} style={{ marginBottom: 24, color: '#1e293b' }}>
        <RocketOutlined style={{ marginRight: 8, color: '#1890ff' }} />
        CodeRunner 快速部署教程
      </Title>

      <Alert
        message="两步完成部署"
        description="本教程将指导您通过两个简单步骤完成CodeRunner的部署和公网访问配置。整个过程大约需要5分钟。"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <div style={{ background: '#f8fafc', borderRadius: 12, padding: 24, border: '1px solid #e2e8f0' }}>
        <Tabs
          defaultActiveKey="aliyun"
          items={[
            {
              key: 'aliyun',
              label: '步骤1：Docker部署（推荐）',
              children: (
                <div>
                  <Title level={5} style={{ color: '#1e293b', marginBottom: 16 }}>
                    步骤1：使用阿里云镜像部署
                  </Title>

                  <Paragraph style={{ color: '#64748b', marginBottom: 20 }}>
                    使用预构建的阿里云镜像快速部署CodeRunner：
                  </Paragraph>

                  <Space direction="vertical" style={{ width: '100%' }}>
                    <CommandBlock
                      command="docker pull crpi-6j8qwz5vgwdd7tds.cn-beijing.personal.cr.aliyuncs.com/coderunner/coderunner:backend"
                      description="拉取后端镜像"
                    />
                    <CommandBlock
                      command="docker run -d --name coderunner_backend -p 8000:8000 -v $(pwd)/data:/app/data -e DATABASE_URL=sqlite:///./data/coderunner.db -e SECRET_KEY=your-secret-key-change-this crpi-6j8qwz5vgwdd7tds.cn-beijing.personal.cr.aliyuncs.com/coderunner/coderunner:backend"
                      description="启动后端服务"
                    />
                  </Space>

                  <Alert
                    message="注意事项"
                    description={
                      <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                        <li>请确保修改 <code>SECRET_KEY</code> 为安全的随机字符串</li>
                        <li>数据目录 <code>$(pwd)/data</code> 将挂载到宿主机，确保数据持久化</li>
                        <li>默认管理员账号：admin / admin123（首次登录后请修改密码）</li>
                      </ul>
                    }
                    type="warning"
                    showIcon
                    style={{ marginTop: 20 }}
                  />
                </div>
              )
            },
            {
              key: 'tunnel',
              label: (
                <span>
                  <ThunderboltOutlined style={{ marginRight: 4 }} />
                  步骤2：HTTPS隧道配置
                </span>
              ),
              children: (
                <div>
                  <Title level={5} style={{ color: '#1e293b', marginBottom: 16 }}>
                    步骤2：打通HTTPS隧道（公网访问）
                  </Title>

                  <Alert
                    message="公网访问配置"
                    description="使用Cloudflare Tunnel为您的CodeRunner服务创建公网HTTPS访问地址，以避免出现一些网络环境下无法访问的问题。"
                    type="info"
                    showIcon
                    style={{ marginBottom: 20 }}
                  />

                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Title level={5} style={{ color: '#059669', marginBottom: 12 }}>
                        <GlobalOutlined style={{ marginRight: 8 }} />
                        第一步：安装cloudflared
                      </Title>
                      <CommandBlock
                        command="mkdir -p ~/cf && cd ~/cf && wget -qO cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && sudo dpkg -i cloudflared.deb && rm cloudflared.deb"
                        description="安装Cloudflare隧道工具"
                      />
                    </div>

                    <div>
                      <Title level={5} style={{ color: '#059669', marginBottom: 12 }}>
                        <GlobalOutlined style={{ marginRight: 8 }} />
                        第二步：启动隧道并获取公网地址
                      </Title>
                      <CommandBlock
                        command="cd ~/cf && nohup cloudflared tunnel --url http://localhost:8000 > tunnel.log 2>&1 & sleep 8 && grep -oP 'https://[^\s]+\.trycloudflare\.com' tunnel.log || tail -20 tunnel.log"
                        description="后台启动隧道服务并显示公网地址"
                      />
                    </div>
                  </Space>

                  <Alert
                    message="使用说明"
                    description={
                      <div>
                        <p><strong>注意事项：</strong></p>
                        <ul style={{ marginBottom: 12 }}>
                          <li>确保您的Docker服务已在 <code>localhost:8000</code> 端口运行</li>
                          <li>隧道地址是临时的，重启服务后会变化</li>
                          <li>生成的HTTPS地址可以直接用于前端配置</li>
                          <li>如需固定域名，请注册Cloudflare账户并创建持久隧道</li>
                        </ul>
                      </div>
                    }
                    type="success"
                    showIcon
                    style={{ marginTop: 20 }}
                  />
                </div>
              )
            },
            {
              key: 'contact',
              label: '项目支持',
              children: (
                <div style={{ textAlign: 'center', padding: '20px' }}>
                  <Title level={5} style={{ color: '#1e293b', marginBottom: 24 }}>
                    项目联系方式
                  </Title>

                  <div style={{
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    marginBottom: 24
                  }}>
                    <a
                      href="https://github.com/qfpqhyl"
                      target="_blank"
                      rel="noopener noreferrer"
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        textDecoration: 'none',
                        color: '#1890ff',
                        padding: '12px 24px',
                        borderRadius: '8px',
                        border: '1px solid #d9d9d9',
                        transition: 'all 0.3s ease'
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.borderColor = '#1890ff';
                        e.currentTarget.style.boxShadow = '0 2px 8px rgba(24, 144, 255, 0.2)';
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.borderColor = '#d9d9d9';
                        e.currentTarget.style.boxShadow = 'none';
                      }}
                    >
                      <img
                        src="https://avatars.githubusercontent.com/u/95489429?v=4"
                        alt="GitHub Avatar"
                        style={{
                          width: '48px',
                          height: '48px',
                          borderRadius: '50%',
                          marginRight: '12px'
                        }}
                        onError={(e) => {
                          e.target.src = 'https://github.com/github.png';
                        }}
                      />
                      <div style={{ textAlign: 'left' }}>
                        <div style={{
                          fontWeight: 'bold',
                          fontSize: '16px',
                          marginBottom: '4px'
                        }}>
                          qfpqhyl
                        </div>
                        <div style={{
                          fontSize: '14px',
                          color: '#666'
                        }}>
                          GitHub Profile
                        </div>
                      </div>
                    </a>
                  </div>

                  <Alert
                    message="项目支持"
                    description={
                      <div>
                        <p>如有问题或建议，欢迎通过GitHub联系我们：</p>
                        <p><strong>GitHub:</strong>
                          <a href="https://github.com/qfpqhyl"
                             target="_blank"
                             rel="noopener noreferrer"
                             style={{ color: '#1890ff', marginLeft: '8px' }}>
                            github.com/qfpqhyl
                          </a>
                        </p>
                        <p style={{ marginTop: '12px', marginBottom: 0 }}>
                          我们会及时回复您的消息并提供技术支持。
                        </p>
                      </div>
                    }
                    type="info"
                    showIcon
                  />
                </div>
              )
            }
          ]}
        />

        <Divider />

        <div style={{ textAlign: 'center', marginTop: 24 }}>
          <Title level={4} style={{ color: '#059669', marginBottom: 8 }}>
            <CheckCircleOutlined style={{ marginRight: 8 }} />
            部署完成！
          </Title>
          <Paragraph style={{ color: '#64748b' }}>
            现在您可以在右侧配置后端地址，然后开始使用 CodeRunner。
          </Paragraph>
          <Space direction="vertical" size="small">
            <div>
              <Text strong style={{ color: '#1890ff' }}>本地访问：</Text>
              <div style={{ marginTop: 4 }}>
                <Tag color="processing">后端API: http://localhost:8000</Tag>
                <Tag color="default">API文档: http://localhost:8000/docs</Tag>
              </div>
            </div>
            <div>
              <Text strong style={{ color: '#52c41a' }}>公网访问（如配置隧道）：</Text>
              <div style={{ marginTop: 4 }}>
                <Tag color="success">后端API: https://your-tunnel.com</Tag>
                <Tag color="default">API文档: https://your-tunnel.com/docs</Tag>
              </div>
            </div>
          </Space>
        </div>
      </div>
    </div>
  );
};

export default DeploymentTutorial;