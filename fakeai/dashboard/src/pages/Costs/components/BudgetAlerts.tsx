/**
 * Budget Alerts Component
 * Displays budget alerts and thresholds
 */

import React, { useState } from 'react';
import { BudgetAlert } from '../types';

interface BudgetAlertsProps {
  totalCost: number;
  dailyAverage: number;
}

export const BudgetAlerts: React.FC<BudgetAlertsProps> = ({ totalCost, dailyAverage }) => {
  const [dailyBudget, setDailyBudget] = useState(100);
  const [monthlyBudget, setMonthlyBudget] = useState(3000);

  const formatCost = (cost: number) => `$${cost.toFixed(2)}`;

  const dailyUsage = (dailyAverage / dailyBudget) * 100;
  const monthlyProjected = dailyAverage * 30;
  const monthlyUsage = (monthlyProjected / monthlyBudget) * 100;

  const getAlertLevel = (usage: number): 'safe' | 'warning' | 'critical' => {
    if (usage >= 90) return 'critical';
    if (usage >= 75) return 'warning';
    return 'safe';
  };

  const dailyLevel = getAlertLevel(dailyUsage);
  const monthlyLevel = getAlertLevel(monthlyUsage);

  return (
    <div className="budget-alerts-container">
      <h3 className="section-title">Budget Alerts</h3>

      <div className="budget-settings">
        <div className="budget-input">
          <label>Daily Budget:</label>
          <input
            type="number"
            value={dailyBudget}
            onChange={(e) => setDailyBudget(Number(e.target.value))}
            min="0"
            step="10"
          />
        </div>
        <div className="budget-input">
          <label>Monthly Budget:</label>
          <input
            type="number"
            value={monthlyBudget}
            onChange={(e) => setMonthlyBudget(Number(e.target.value))}
            min="0"
            step="100"
          />
        </div>
      </div>

      <div className="budget-status">
        <div className={`budget-card ${dailyLevel}`}>
          <div className="budget-header">
            <h4>Daily Budget</h4>
            {dailyLevel === 'critical' && <span className="alert-badge">Alert</span>}
            {dailyLevel === 'warning' && <span className="warning-badge">Warning</span>}
          </div>
          <div className="budget-progress">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${Math.min(dailyUsage, 100)}%` }}
              ></div>
            </div>
            <div className="progress-label">{dailyUsage.toFixed(1)}%</div>
          </div>
          <div className="budget-details">
            <span>{formatCost(dailyAverage)} / {formatCost(dailyBudget)}</span>
          </div>
        </div>

        <div className={`budget-card ${monthlyLevel}`}>
          <div className="budget-header">
            <h4>Monthly Projection</h4>
            {monthlyLevel === 'critical' && <span className="alert-badge">Alert</span>}
            {monthlyLevel === 'warning' && <span className="warning-badge">Warning</span>}
          </div>
          <div className="budget-progress">
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${Math.min(monthlyUsage, 100)}%` }}
              ></div>
            </div>
            <div className="progress-label">{monthlyUsage.toFixed(1)}%</div>
          </div>
          <div className="budget-details">
            <span>{formatCost(monthlyProjected)} / {formatCost(monthlyBudget)}</span>
          </div>
        </div>
      </div>

      {(dailyLevel !== 'safe' || monthlyLevel !== 'safe') && (
        <div className="alert-messages">
          {dailyLevel === 'critical' && (
            <div className="alert-message critical">
              Daily spending is at {dailyUsage.toFixed(0)}% of budget. Immediate action recommended.
            </div>
          )}
          {dailyLevel === 'warning' && (
            <div className="alert-message warning">
              Daily spending is at {dailyUsage.toFixed(0)}% of budget. Monitor closely.
            </div>
          )}
          {monthlyLevel === 'critical' && (
            <div className="alert-message critical">
              Projected monthly cost exceeds budget by {formatCost(monthlyProjected - monthlyBudget)}.
            </div>
          )}
        </div>
      )}
    </div>
  );
};
