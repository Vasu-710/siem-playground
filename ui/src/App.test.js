import { render, screen, waitFor } from '@testing-library/react';
import App from './App';

function mockAlerts(alerts) {
  global.fetch = jest.fn(() =>
    Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(alerts) })
  );
}

afterEach(() => {
  jest.restoreAllMocks();
  delete global.fetch;
});

test('renders alerts returned by the collector', async () => {
  mockAlerts([
    { id: 1, name: 'Credential Submission', severity: 7, evidence: {}, enrichment: {} },
  ]);

  render(<App />);

  expect(await screen.findByText('Credential Submission')).toBeInTheDocument();
  expect(screen.getAllByText(/HIGH/).length).toBeGreaterThan(0);
});

test('shows the empty state when there are no alerts', async () => {
  mockAlerts([]);

  render(<App />);

  expect(await screen.findByText('No Alerts Detected')).toBeInTheDocument();
});

test('surfaces a failed request instead of showing a clean dashboard', async () => {
  global.fetch = jest.fn(() => Promise.resolve({ ok: false, status: 503 }));

  render(<App />);

  await waitFor(() => expect(screen.getByText(/503/)).toBeInTheDocument());
});

test('surfaces a network error', async () => {
  global.fetch = jest.fn(() => Promise.reject(new Error('connection refused')));

  render(<App />);

  await waitFor(() => expect(screen.getByText(/connection refused/)).toBeInTheDocument());
});

test('counts the alerts it was given', async () => {
  mockAlerts([
    { id: 1, name: 'A', severity: 9, evidence: {}, enrichment: {} },
    { id: 2, name: 'B', severity: 5, evidence: {}, enrichment: {} },
  ]);

  render(<App />);

  await screen.findByText('A');
  expect(screen.getByText('TOTAL ALERTS').nextSibling).toHaveTextContent('2');
});
