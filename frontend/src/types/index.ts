export interface GeneratorAttribution {
  attributed_family: string;
  confidence: number;
  family_probabilities: {
    'Midjourney'?: number;
    'Stable Diffusion'?: number;
    'FLUX.1'?: number;
    'DALL-E 3'?: number;
    'GAN/StyleGAN'?: number;
    'Authentic/Camera'?: number;
    [key: string]: number | undefined;
  };
  is_unseen_architecture: boolean;
  notes: string;
}

export interface MetadataProvenance {
  has_exif: boolean;
  c2pa_manifest_found: boolean;
  c2pa_claim_summary: string | null;
  exif_details: {
    make?: string;
    model?: string;
    lens?: string;
    iso?: string | number;
    exposure?: string;
    focal_length?: string;
    software?: string;
    modify_date?: string;
    [key: string]: any;
  };
  authenticity_signals: {
    has_camera_hardware_signature?: boolean;
    has_ai_generation_software_tag?: boolean;
    has_cryptographic_c2pa_manifest?: boolean;
    compression_consistency?: string;
    [key: string]: any;
  };
}

export interface AnalysisResult {
  id?: string;
  image_name: string;
  prediction: string; // e.g. "Likely AI-generated" or "Likely Authentic Real"
  is_ai_generated: boolean;
  raw_probability_ai: number;
  calibrated_confidence: number;
  confidence_percentage: number;
  explanation: string;
  gradcam_heatmap: string; // base64
  convnext_features_summary?: {
    mean_activation?: number;
    variance?: number;
    anomaly_score?: number;
    layer_norm?: number;
    [key: string]: any;
  };
  generator_attribution: GeneratorAttribution;
  metadata_provenance: MetadataProvenance;
  preview_url?: string;
  timestamp?: string;
}

export interface BatchAnalysisResponse {
  total_analyzed: number;
  results: AnalysisResult[];
}

export interface RobustnessTestResult {
  test_type: string;
  parameter: string;
  original_prediction: string;
  perturbed_prediction: string;
  prediction_consistent: boolean;
  confidence_drift: number;
  details?: string;
}

export interface ModelMetrics {
  primary_metric_name?: string;
  primary_metric?: string;
  unseen_generator_roc_auc?: number;
  unseen_roc_auc?: number;
  overall_roc_auc: number;
  macro_f1_score?: number;
  macro_f1?: number;
  false_positive_rate: number;
  accuracy: number;
  confusion_matrix?: any;
  backbone_architecture?: string;
  unseen_generators_tested?: string[];
  evaluated_generators?: string[];
}

export type PaginationMode = 'cylinder' | 'stack' | 'scrubber' | 'grid';

export type ActiveTab = 'workbench' | 'batch' | 'robustness' | 'provenance' | 'benchmarks';
