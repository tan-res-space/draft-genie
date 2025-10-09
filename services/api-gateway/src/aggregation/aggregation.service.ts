import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import { ProxyService, ServiceType } from '../proxy/proxy.service';

interface AggregatedSection<T> {
  data: T | null;
  error: string | null;
}

interface DashboardSummary {
  totalSpeakers: number;
  totalDrafts: number;
  totalEvaluations: number;
  servicesHealthy: number;
  servicesTotal: number;
  healthPercentage: number;
}

interface DashboardAggregationResult {
  speakers: AggregatedSection<any>;
  evaluations: AggregatedSection<any>;
  drafts: AggregatedSection<any>;
  aggregatedAt: string;
  summary?: DashboardSummary;
}

@Injectable()
export class AggregationService {
  private readonly logger = new Logger(AggregationService.name);

  constructor(private readonly proxyService: ProxyService) {}

  /**
   * Get complete speaker data with drafts and evaluations
   * Aggregates data from Speaker, Draft, and Evaluation services
   */
  async getSpeakerComplete(speakerId: string): Promise<any> {
    this.logger.log(`Aggregating complete data for speaker ${speakerId}`);

    try {
      // Fetch data from all services in parallel
      const [speaker, drafts, evaluations, metrics] = await Promise.allSettled([
        this.proxyService.get(ServiceType.SPEAKER, `/api/v1/speakers/${speakerId}`),
        this.proxyService.get(ServiceType.DRAFT, `/api/v1/drafts/speaker/${speakerId}`),
        this.proxyService.get(ServiceType.SPEAKER, `/api/v1/speakers/${speakerId}/evaluations`),
        this.proxyService.get(ServiceType.EVALUATION, `/api/v1/metrics/speaker/${speakerId}`),
      ]);

      // Handle speaker data (required)
      if (speaker.status === 'rejected') {
        throw new NotFoundException(`Speaker with ID ${speakerId} not found`);
      }

      // Build aggregated response
      const result: any = {
        speaker: speaker.status === 'fulfilled' ? speaker.value : null,
        drafts: {
          data: drafts.status === 'fulfilled' ? drafts.value : [],
          error: drafts.status === 'rejected' ? 'Failed to fetch drafts' : null,
        },
        evaluations: {
          data: evaluations.status === 'fulfilled' ? evaluations.value : [],
          error: evaluations.status === 'rejected' ? 'Failed to fetch evaluations' : null,
        },
        metrics: {
          data: metrics.status === 'fulfilled' ? metrics.value : null,
          error: metrics.status === 'rejected' ? 'Failed to fetch metrics' : null,
        },
        aggregatedAt: new Date().toISOString(),
      };

      // Add summary statistics
      if (result.drafts.data && Array.isArray(result.drafts.data)) {
        result.summary = {
          totalDrafts: result.drafts.data.length,
          totalEvaluations: Array.isArray(result.evaluations.data) ? result.evaluations.data.length : 0,
          hasMetrics: !!result.metrics.data,
        };
      }

      return result;
    } catch (error) {
      this.logger.error(`Error aggregating speaker data: ${error.message}`);
      throw error;
    }
  }

  /**
   * Get dashboard metrics aggregated from multiple services
   */
  async getDashboardMetrics(): Promise<any> {
    this.logger.log('Aggregating dashboard metrics');

    try {
      // Fetch metrics from all services in parallel
      const [speakerStats, evaluationMetrics, draftStats] = await Promise.allSettled([
        this.proxyService.get(ServiceType.SPEAKER, '/api/v1/speakers/statistics'),
        this.proxyService.get(ServiceType.EVALUATION, '/api/v1/metrics'),
        this.fetchDraftStatistics(),
      ]);

      const result: DashboardAggregationResult = {
        speakers: {
          data: speakerStats.status === 'fulfilled' ? speakerStats.value : null,
          error: speakerStats.status === 'rejected' ? 'Failed to fetch speaker statistics' : null,
        },
        evaluations: {
          data: evaluationMetrics.status === 'fulfilled' ? evaluationMetrics.value : null,
          error: evaluationMetrics.status === 'rejected' ? 'Failed to fetch evaluation metrics' : null,
        },
        drafts: {
          data: draftStats.status === 'fulfilled' ? draftStats.value : null,
          error: draftStats.status === 'rejected' ? 'Failed to fetch draft statistics' : null,
        },
        aggregatedAt: new Date().toISOString(),
      };

      // Calculate overall summary
      result.summary = this.calculateOverallSummary(result);

      return result;
    } catch (error) {
      this.logger.error(`Error aggregating dashboard metrics: ${error.message}`);
      throw error;
    }
  }

  /**
   * Fetch draft statistics (custom aggregation since Draft Service may not have a stats endpoint)
   */
  private async fetchDraftStatistics(): Promise<any> {
    try {
      // Get all drafts and calculate statistics
      const drafts = await this.proxyService.get(ServiceType.DRAFT, '/api/v1/drafts');
      
      if (!Array.isArray(drafts)) {
        return { total: 0, byStatus: {} };
      }

      const stats = {
        total: drafts.length,
        byStatus: drafts.reduce((acc, draft) => {
          const status = draft.status || 'unknown';
          acc[status] = (acc[status] || 0) + 1;
          return acc;
        }, {}),
      };

      return stats;
    } catch (error) {
      this.logger.warn(`Failed to fetch draft statistics: ${error.message}`);
      return { total: 0, byStatus: {}, error: error.message };
    }
  }

  /**
   * Calculate overall summary from aggregated data
   */
  private calculateOverallSummary(data: DashboardAggregationResult): DashboardSummary {
    const summary: DashboardSummary = {
      totalSpeakers: 0,
      totalDrafts: 0,
      totalEvaluations: 0,
      servicesHealthy: 0,
      servicesTotal: 3,
      healthPercentage: 0,
    };

    // Count speakers
    if (data.speakers.data && !data.speakers.error) {
      summary.totalSpeakers = data.speakers.data.total || 0;
      summary.servicesHealthy++;
    }

    // Count drafts
    if (data.drafts.data && !data.drafts.error) {
      summary.totalDrafts = data.drafts.data.total || 0;
      summary.servicesHealthy++;
    }

    // Count evaluations
    if (data.evaluations.data && !data.evaluations.error) {
      summary.totalEvaluations = Array.isArray(data.evaluations.data) 
        ? data.evaluations.data.length 
        : 0;
      summary.servicesHealthy++;
    }

    summary.healthPercentage = Math.round((summary.servicesHealthy / summary.servicesTotal) * 100);

    return summary;
  }
}
