export interface Step {
  id: number;
  description: string;
  is_completed: boolean;
  step_order: number;
}

export interface Goal {
  id: number;
  title: string;
  description?: string;
  status: 'active' | 'completed' | 'failed';
  metric_label?: string;
  metric_target?: number;
  metric_current?: number;
  steps: Step[];
  deadline?: string;
}

export interface CharacterState {
  emotion: 'happy' | 'worried' | 'panicked';
  tokens: number;
  streak: number;
}