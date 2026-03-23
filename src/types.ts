export type Lang = "en" | "zh";

export type AuditMode = "official" | "fragile" | "audit";

export type ViewMode = "popular" | "expert";

export type PathologyTag =
  | "acm-recovered"
  | "distance-sensitive"
  | "geometry-fragile"
  | "MOND-resistant"
  | "gas-flat"
  | "stellar-hostage";

export type Verdict = "acm" | "mond" | "ambiguous";

export interface GalaxyRecord {
  id: string;
  displayName: string;
  winner: Verdict;
  confidence: "high" | "medium" | "fragile";
  primarySensitivity: "distance" | "inclination" | "shape-depth" | "mass-normalization";
  pathologyTags: PathologyTag[];
  distanceMpc: number;
  distanceErrorMpc: number;
  inclinationDeg: number;
  geometryFlag: string;
  acmCpp: number;
  mondCpp: number;
  profilePath?: string;
  structure: {
    l36: number;
    gasToLightProxy: number;
    outerGasSlope: number;
    outerGasCurvature: number;
    outerToInnerGasRatio: number;
  };
  profile: {
    radiusKpc: number[];
    vObs: number[];
    vObsErr: number[];
    vAcm: number[];
    vMond: number[];
    vGas: number[];
    vDisk: number[];
    vBulge: number[];
  };
}
