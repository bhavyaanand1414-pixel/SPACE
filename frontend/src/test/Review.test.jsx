import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ReviewPage } from '../pages/ReviewPage';

describe('Human-In-The-Loop Review Queue & Active Learning Staging', () => {
  it('renders review queue header and safety banner', () => {
    render(
      <BrowserRouter>
        <ReviewPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/Human-in-the-Loop Review Queue/i)).toBeInTheDocument();
    expect(screen.getByText(/Active Learning Safety Policy/i)).toBeInTheDocument();
    expect(screen.getByText(/Export Active Learning Candidates/i)).toBeInTheDocument();
  });

  it('renders review filter tabs and table rows', () => {
    render(
      <BrowserRouter>
        <ReviewPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/All Items/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Pending Review/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/CR-007/i)).toBeInTheDocument();
    expect(screen.getByText(/Construction Site/i)).toBeInTheDocument();
  });

  it('opens human correction modal on Review click', () => {
    render(
      <BrowserRouter>
        <ReviewPage />
      </BrowserRouter>
    );

    const reviewBtns = screen.getAllByText(/Review \/ Override/i);
    fireEvent.click(reviewBtns[0]);

    expect(screen.getByText(/Human Verification & Correction/i)).toBeInTheDocument();
    expect(screen.getByText(/Level 1 Category Override:/i)).toBeInTheDocument();
    expect(screen.getByText(/Save Human Correction & Audit Trail/i)).toBeInTheDocument();
  });

  it('renders interactive satellite chip inspection, spectral indicators, and hotkey controls in modal', () => {
    render(
      <BrowserRouter>
        <ReviewPage />
      </BrowserRouter>
    );

    const reviewBtns = screen.getAllByText(/Review \/ Override/i);
    fireEvent.click(reviewBtns[0]);

    // Satellite chip inspection elements
    expect(screen.getByText(/Multi-Temporal Satellite Chip Inspection/i)).toBeInTheDocument();
    expect(screen.getByText(/T1: BASELINE/i)).toBeInTheDocument();
    expect(screen.getByText(/T2: POST-EVENT/i)).toBeInTheDocument();

    // Multi-spectral corroboration telemetry
    expect(screen.getByText(/ΔNDVI \(Vegetation\)/i)).toBeInTheDocument();
    expect(screen.getByText(/ΔNDBI \(Built-Up\)/i)).toBeInTheDocument();
    expect(screen.getByText(/SAR Backscatter σ⁰/i)).toBeInTheDocument();

    // Toolbar buttons
    expect(screen.getByText(/2Hz Flicker Mode/i)).toBeInTheDocument();
    expect(screen.getByText(/AI Mask ON/i)).toBeInTheDocument();
    expect(screen.getByText(/HOTKEYS:/i)).toBeInTheDocument();
    expect(screen.getByText(/Confirm Prediction \[A\]/i)).toBeInTheDocument();

    // Toggle flicker mode
    const flickerBtn = screen.getByText(/2Hz Flicker Mode/i);
    fireEvent.click(flickerBtn);
    expect(screen.getByText(/Flicker Mode \[ACTIVE\]/i)).toBeInTheDocument();

    // Toggle AI Mask
    const maskBtn = screen.getByText(/AI Mask ON/i);
    fireEvent.click(maskBtn);
    expect(screen.getByText(/AI Mask OFF/i)).toBeInTheDocument();
  });
});
