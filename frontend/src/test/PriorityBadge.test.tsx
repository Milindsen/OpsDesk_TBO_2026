import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { PriorityBadge } from '../components/PriorityBadge';

describe('PriorityBadge Component', () => {
  it('renders P1 badge with red-600 color class', () => {
    render(<PriorityBadge priority="P1" />);
    const badge = screen.getByTestId('priority-badge-P1');
    expect(badge).toHaveTextContent('P1');
    expect(badge.className).toContain('red-600');
  });

  it('renders P2 badge with orange-500 color class', () => {
    render(<PriorityBadge priority="P2" />);
    const badge = screen.getByTestId('priority-badge-P2');
    expect(badge).toHaveTextContent('P2');
    expect(badge.className).toContain('orange-500');
  });

  it('renders P3 badge with blue-500 color class', () => {
    render(<PriorityBadge priority="P3" />);
    const badge = screen.getByTestId('priority-badge-P3');
    expect(badge).toHaveTextContent('P3');
    expect(badge.className).toContain('blue-500');
  });

  it('renders P4 badge with gray-400 color class', () => {
    render(<PriorityBadge priority="P4" />);
    const badge = screen.getByTestId('priority-badge-P4');
    expect(badge).toHaveTextContent('P4');
    expect(badge.className).toContain('gray-400');
  });
});
