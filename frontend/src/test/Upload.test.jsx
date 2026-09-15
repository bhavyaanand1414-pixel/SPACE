import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { UploadPage } from '../pages/UploadPage';

describe('UploadPage 1-Click Demo Sample Presets', () => {
  it('renders 1-click sample presets card with 3 selectable datasets', () => {
    render(
      <BrowserRouter>
        <UploadPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/1-Click Demo Sample Satellite Pairs/i)).toBeInTheDocument();
    expect(screen.getByText(/Guwahati Urban Sprawl/i)).toBeInTheDocument();
    expect(screen.getByText(/Brahmaputra Flood Dynamics/i)).toBeInTheDocument();
    expect(screen.getByText(/Karbi Anglong Forest Canopy/i)).toBeInTheDocument();
  });

  it('clicking Guwahati Urban Sprawl populates slots and renders quality score', () => {
    render(
      <BrowserRouter>
        <UploadPage />
      </BrowserRouter>
    );

    const presetBtn = screen.getByText(/Guwahati Urban Sprawl/i);
    fireEvent.click(presetBtn);

    // Both observation slots must indicate raster ingested
    const ingestedBadges = screen.getAllByText(/Raster Ingested & Validated/i);
    expect(ingestedBadges.length).toBe(2);

    // Quality Score and Verification checks must appear
    expect(screen.getByText(/94 \/ 100/i)).toBeInTheDocument();
    expect(screen.getByText(/READY_FOR_INFERENCE/i)).toBeInTheDocument();
    expect(screen.getByText(/Coordinate Reference System \(CRS\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Proceed to Siamese U-Net Analysis/i)).toBeInTheDocument();
  });

  it('clicking Brahmaputra Flood Dynamics switches to SAR modality with 91 score', () => {
    render(
      <BrowserRouter>
        <UploadPage />
      </BrowserRouter>
    );

    const floodBtn = screen.getByText(/Brahmaputra Flood Dynamics/i);
    fireEvent.click(floodBtn);

    expect(screen.getByText(/91 \/ 100/i)).toBeInTheDocument();
    expect(screen.getByText(/C-Band SAR Modality/i)).toBeInTheDocument();
  });

  it('clicking Reset Dropzones clears all slots and validation matrix', () => {
    render(
      <BrowserRouter>
        <UploadPage />
      </BrowserRouter>
    );

    // Load first
    fireEvent.click(screen.getByText(/Guwahati Urban Sprawl/i));
    expect(screen.getByText(/94 \/ 100/i)).toBeInTheDocument();

    // Now click reset
    const resetBtn = screen.getByText(/Reset Dropzones/i);
    fireEvent.click(resetBtn);

    // After reset, no quality score should be visible
    expect(screen.queryByText(/94 \/ 100/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Raster Ingested & Validated/i)).not.toBeInTheDocument();
  });
});
