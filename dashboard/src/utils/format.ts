import { format, formatDistanceToNow } from 'date-fns';

export function formatTimestamp(timestamp: number): string {
  return format(new Date(timestamp * 1000), 'MMM d, yyyy HH:mm:ss');
}

export function formatRelativeTime(timestamp: number): string {
  return formatDistanceToNow(new Date(timestamp * 1000), { addSuffix: true });
}

export function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;
  
  if (hours > 0) {
    return hours + 'h ' + minutes + 'm ' + secs + 's';
  } else if (minutes > 0) {
    return minutes + 'm ' + secs + 's';
  } else {
    return secs + 's';
  }
}

export function formatCost(cost: number): string {
  return '$' + cost.toFixed(4);
}

export function formatTokens(tokens: number): string {
  if (tokens >= 1000000) {
    return (tokens / 1000000).toFixed(2) + 'M';
  } else if (tokens >= 1000) {
    return (tokens / 1000).toFixed(2) + 'K';
  }
  return tokens.toString();
}
