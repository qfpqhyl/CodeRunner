import React from 'react';
import { Avatar, Space, Typography, Button } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import moment from 'moment';

const { Text } = Typography;

const Comment = ({ author, avatar, content, actions, datetime, children }) => {
  return (
    <div style={{ marginBottom: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start' }}>
        <div style={{ marginRight: '12px', flexShrink: 0 }}>
          {avatar || <Avatar icon={<UserOutlined />} />}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ marginBottom: '4px' }}>
            <Space>
              {typeof author === 'string' ? (
                <Text strong>{author}</Text>
              ) : (
                author
              )}
              {datetime && (
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {typeof datetime === 'string' ? datetime : moment(datetime).fromNow()}
                </Text>
              )}
            </Space>
          </div>
          <div style={{ marginBottom: '8px' }}>
            {content}
          </div>
          {actions && actions.length > 0 && (
            <div>
              <Space size="small">
                {actions.map((action, index) => (
                  <Button
                    key={index}
                    type="text"
                    size="small"
                    style={{ fontSize: '12px', height: 'auto', padding: '0 4px' }}
                    {...(typeof action === 'object' ? action : {})}
                  >
                    {action}
                  </Button>
                ))}
              </Space>
            </div>
          )}
          {children && (
            <div style={{ marginTop: '16px', marginLeft: '48px' }}>
              {children}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Comment;