import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { SLAChip } from '../components/SLAChip';

describe('SLAChip Component', () => {
  it('renders "On Track" for ok status', () => {
    render(<SLAChip status="ok" />);
    expect(screen.getByText(/On Track/i)).toBeInTheDocument();
  });

  it('renders "At Risk" for at_risk status', () => {
    render(<SLAChip status="at_risk" />);
    expect(screen.getByText(/At Risk/i)).toBeInTheDocument();
  });

  it('renders "Breached" for breached status', () => {
    render(<SLAChip status="breached" />);
    expect(screen.getByText(/Breached/i)).toBeInTheDocument();
  });
});
