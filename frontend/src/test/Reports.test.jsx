import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ReportsPage } from '../pages/ReportsPage';

describe('Geospatial PDF Reports Studio', () => {
  it('renders report header, statistics cards, and disclaimer', () => {
    render(
      <BrowserRouter>
        <ReportsPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/Automated Geospatial Intelligence Reports/i)).toBeInTheDocument();
    expect(screen.getByText(/REPORTLAB ENGINE/i)).toBeInTheDocument();
    expect(screen.getByText(/104.85 km²/i)).toBeInTheDocument();
    expect(screen.getByText(/5.24 km²/i)).toBeInTheDocument();
    expect(screen.getByText(/ISRO SIH1518 Mandatory Scientific Advisory Disclaimer/i)).toBeInTheDocument();
  });

  it('renders compile report button and reports list table', () => {
    render(
      <BrowserRouter>
        <ReportsPage />
      </BrowserRouter>
    );

    expect(screen.getByText(/Generate New PDF Report/i)).toBeInTheDocument();
    expect(screen.getByText(/Guwahati Multi-Temporal Satellite Change Intelligence Dossier/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Download PDF/i).length).toBeGreaterThan(0);
  });
});
