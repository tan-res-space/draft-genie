// Value objects for domain-driven design

export class SER {
  constructor(public readonly value: number) {
    if (value < 0 || value > 1) {
      throw new Error('SER must be between 0 and 1');
    }
  }

  toPercentage(): number {
    return this.value * 100;
  }

  static fromPercentage(percentage: number): SER {
    return new SER(percentage / 100);
  }
}

export class WER {
  constructor(public readonly value: number) {
    if (value < 0 || value > 1) {
      throw new Error('WER must be between 0 and 1');
    }
  }

  toPercentage(): number {
    return this.value * 100;
  }

  static fromPercentage(percentage: number): WER {
    return new WER(percentage / 100);
  }
}

export class QualityScore {
  constructor(public readonly value: number) {
    if (value < 0 || value > 1) {
      throw new Error('Quality score must be between 0 and 1');
    }
  }

  toPercentage(): number {
    return this.value * 100;
  }

  static fromPercentage(percentage: number): QualityScore {
    return new QualityScore(percentage / 100);
  }
}

