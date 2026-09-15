import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

describe('Frontend App Layout & Navigation', () => {
  it('renders application navigation and header title', () => {
    render(<App />);
    expect(screen.getAllByText(/ISRO/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/SIH1518/i).length).toBeGreaterThan(0);
  });

  it('renders all key navigation links in the sidebar', () => {
    render(<App />);
    expect(screen.getAllByText(/Dashboard/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Upload Imagery/i)).toBeInTheDocument();
    expect(screen.getByText(/Interactive GIS Map/i)).toBeInTheDocument();
    expect(screen.getByText(/Change Results/i)).toBeInTheDocument();
    expect(screen.getByText(/Time-Series/i)).toBeInTheDocument();
    expect(screen.getAllByText(/PDF Reports/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/Human Review Queue/i)).toBeInTheDocument();
    expect(screen.getByText(/AI Agent Portal/i)).toBeInTheDocument();
  });
});
