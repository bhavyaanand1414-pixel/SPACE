import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AgentPage } from '../pages/AgentPage';

describe('AI Satellite Intelligence Agent Interface', () => {
  it('renders agent header and anti-hallucination badge', () => {
    render(
      <BrowserRouter>
        <AgentPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/AI Satellite Intelligence Agent/i)).toBeInTheDocument();
    expect(screen.getByText(/ANTI-HALLUCINATION ACTIVE/i)).toBeInTheDocument();
    expect(screen.getByText(/20 DETERMINISTIC GIS & ML TOOLS/i)).toBeInTheDocument();
  });

  it('renders suggested quick prompt chips', () => {
    render(
      <BrowserRouter>
        <AgentPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/What changed\?/i)).toBeInTheDocument();
    expect(screen.getByText(/Show all new buildings\./i)).toBeInTheDocument();
    expect(screen.getByText(/How much area was flooded\?/i)).toBeInTheDocument();
    expect(screen.getByText(/Generate a report\./i)).toBeInTheDocument();
  });

  it('populates input bar when a prompt chip is clicked', () => {
    render(
      <BrowserRouter>
        <AgentPage />
      </BrowserRouter>
    );

    const promptBtn = screen.getByText(/Show all new buildings\./i);
    fireEvent.click(promptBtn);

    const input = screen.getByPlaceholderText(/Ask questions about detected changes/i);
    expect(input.value).toBe('Show all new buildings.');
  });
});
