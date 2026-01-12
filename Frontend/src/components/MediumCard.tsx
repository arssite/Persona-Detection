import React from 'react';
import { Card, CardContent, Typography, Avatar, Box, Chip, List, ListItem, ListItemText } from '@mui/material';
import { Article, OpenInNew } from '@mui/icons-material';

interface MediumStory {
  title?: string;
  url?: string;
}

interface MediumProfileData {
  username: string;
  url: string;
  name?: string;
  bio?: string;
  followers_count?: number;
  following_count?: number;
  profile_image_url?: string;
  recent_stories?: MediumStory[];
}

interface MediumCardProps {
  profile: MediumProfileData;
}

const MediumCard: React.FC<MediumCardProps> = ({ profile }) => {
  const formatCount = (count?: number) => {
    if (!count) return '—';
    if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}K`;
    }
    return count.toLocaleString();
  };

  return (
    <Card
      sx={{
        background: 'linear-gradient(135deg, #000000 0%, #1a1a1a 100%)',
        color: 'white',
        transition: 'transform 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
        },
      }}
    >
      <CardContent>
        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <Article sx={{ fontSize: 32 }} />
          <Typography variant="h6" fontWeight="bold">
            Medium Profile
          </Typography>
        </Box>

        <Box display="flex" alignItems="center" gap={2} mb={2}>
          <Avatar
            src={profile.profile_image_url || undefined}
            alt={profile.username}
            sx={{ width: 64, height: 64, border: '3px solid #00ab6c' }}
          >
            {profile.username[0]?.toUpperCase()}
          </Avatar>
          <Box flex={1}>
            <Typography variant="h6" fontWeight="bold">
              {profile.name || `@${profile.username}`}
            </Typography>
            {profile.name && (
              <Typography variant="body2" sx={{ opacity: 0.8 }}>
                @{profile.username}
              </Typography>
            )}
          </Box>
        </Box>

        {profile.bio && (
          <Typography
            variant="body2"
            sx={{
              mb: 2,
              opacity: 0.9,
              fontStyle: 'italic',
            }}
          >
            "{profile.bio}"
          </Typography>
        )}

        {(profile.followers_count || profile.following_count) && (
          <Box display="flex" gap={3} mb={2}>
            {profile.followers_count !== undefined && (
              <Box>
                <Typography variant="h6" fontWeight="bold">
                  {formatCount(profile.followers_count)}
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.8 }}>
                  Followers
                </Typography>
              </Box>
            )}
            {profile.following_count !== undefined && (
              <Box>
                <Typography variant="h6" fontWeight="bold">
                  {formatCount(profile.following_count)}
                </Typography>
                <Typography variant="caption" sx={{ opacity: 0.8 }}>
                  Following
                </Typography>
              </Box>
            )}
          </Box>
        )}

        {profile.recent_stories && profile.recent_stories.length > 0 && (
          <Box mb={2}>
            <Typography variant="subtitle2" fontWeight="bold" mb={1} sx={{ color: '#00ab6c' }}>
              Recent Stories
            </Typography>
            <List dense sx={{ bgcolor: 'rgba(255, 255, 255, 0.05)', borderRadius: 1 }}>
              {profile.recent_stories.slice(0, 3).map((story, idx) => (
                <ListItem
                  key={idx}
                  component="a"
                  href={story.url || '#'}
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{
                    cursor: 'pointer',
                    '&:hover': {
                      bgcolor: 'rgba(0, 171, 108, 0.1)',
                    },
                  }}
                >
                  <ListItemText
                    primary={story.title || 'Untitled Story'}
                    primaryTypographyProps={{
                      variant: 'body2',
                      sx: { color: 'white' },
                    }}
                  />
                  <OpenInNew sx={{ fontSize: 16, opacity: 0.6 }} />
                </ListItem>
              ))}
            </List>
          </Box>
        )}

        <Box display="flex" gap={1} flexWrap="wrap">
          <Chip
            label="View Profile"
            size="small"
            component="a"
            href={profile.url}
            target="_blank"
            rel="noopener noreferrer"
            clickable
            sx={{
              bgcolor: '#00ab6c',
              color: 'white',
              fontWeight: 'bold',
              '&:hover': {
                bgcolor: '#00d084',
              },
            }}
          />
        </Box>
      </CardContent>
    </Card>
  );
};

export default MediumCard;
