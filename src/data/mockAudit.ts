import { GalaxyRecord } from "../types";

const radius = [0.5, 1, 2, 4, 6, 8, 10, 14, 18, 24];

export const mockGalaxies: GalaxyRecord[] = [
  {
    id: "UGC00128",
    displayName: "UGC 00128",
    winner: "mond",
    confidence: "fragile",
    primarySensitivity: "distance",
    pathologyTags: ["distance-sensitive", "MOND-resistant"],
    distanceMpc: 64.5,
    distanceErrorMpc: 9.7,
    inclinationDeg: 57,
    geometryFlag: "review",
    acmCpp: 771.68,
    mondCpp: 292.97,
    structure: { l36: 12.02, gasToLightProxy: 0.62, outerGasSlope: 1.18, outerGasCurvature: 5.1, outerToInnerGasRatio: 3.8 },
    profile: {
      radiusKpc: radius,
      vObs: [26, 34, 50, 68, 77, 83, 88, 93, 96, 98],
      vObsErr: [5, 4, 4, 3, 3, 3, 4, 4, 4, 5],
      vAcm: [20, 29, 42, 56, 62, 66, 68, 69, 70, 70],
      vMond: [23, 33, 48, 65, 74, 80, 85, 89, 92, 94],
      vGas: [5, 8, 12, 18, 22, 24, 25, 26, 27, 28],
      vDisk: [12, 18, 26, 34, 38, 39, 39, 38, 37, 35],
      vBulge: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    }
  },
  {
    id: "NGC2841",
    displayName: "NGC 2841",
    winner: "mond",
    confidence: "medium",
    primarySensitivity: "mass-normalization",
    pathologyTags: ["stellar-hostage", "MOND-resistant"],
    distanceMpc: 14.1,
    distanceErrorMpc: 0.8,
    inclinationDeg: 74,
    geometryFlag: "ok",
    acmCpp: 71.76,
    mondCpp: 2.58,
    structure: { l36: 6.54, gasToLightProxy: 2.07, outerGasSlope: 1.35, outerGasCurvature: 8.57, outerToInnerGasRatio: 4.78 },
    profile: {
      radiusKpc: radius,
      vObs: [95, 140, 205, 255, 287, 304, 310, 314, 316, 317],
      vObsErr: [8, 7, 6, 6, 5, 5, 5, 5, 6, 6],
      vAcm: [90, 132, 198, 243, 270, 286, 293, 299, 302, 304],
      vMond: [91, 137, 204, 252, 285, 301, 307, 311, 313, 315],
      vGas: [8, 11, 15, 20, 24, 25, 26, 26, 26, 26],
      vDisk: [58, 91, 132, 166, 185, 193, 196, 197, 197, 196],
      vBulge: [46, 64, 82, 89, 88, 84, 79, 70, 62, 55]
    }
  },
  {
    id: "UGC05764",
    displayName: "UGC 05764",
    winner: "mond",
    confidence: "fragile",
    primarySensitivity: "shape-depth",
    pathologyTags: ["gas-flat", "MOND-resistant", "geometry-fragile"],
    distanceMpc: 7.47,
    distanceErrorMpc: 2.24,
    inclinationDeg: 60,
    geometryFlag: "review",
    acmCpp: 1252.97,
    mondCpp: 137.35,
    structure: { l36: 0.085, gasToLightProxy: 1.92, outerGasSlope: 0.64, outerGasCurvature: 3.31, outerToInnerGasRatio: 5.95 },
    profile: {
      radiusKpc: radius,
      vObs: [12, 18, 24, 30, 35, 39, 42, 46, 49, 51],
      vObsErr: [4, 4, 4, 4, 3, 3, 3, 4, 4, 5],
      vAcm: [10, 15, 20, 25, 28, 30, 31, 31, 31, 31],
      vMond: [11, 17, 23, 29, 34, 38, 41, 44, 47, 49],
      vGas: [4, 7, 10, 13, 16, 18, 19, 20, 20, 20],
      vDisk: [1, 2, 3, 4, 4, 4, 3, 3, 2, 2],
      vBulge: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    }
  },
  {
    id: "NGC5907",
    displayName: "NGC 5907",
    winner: "acm",
    confidence: "high",
    primarySensitivity: "distance",
    pathologyTags: ["acm-recovered"],
    distanceMpc: 17.3,
    distanceErrorMpc: 0.9,
    inclinationDeg: 88,
    geometryFlag: "ok",
    acmCpp: 9.2,
    mondCpp: 505.32,
    structure: { l36: 175.4, gasToLightProxy: 0.12, outerGasSlope: 0.77, outerGasCurvature: 7.62, outerToInnerGasRatio: 4.22 },
    profile: {
      radiusKpc: radius,
      vObs: [140, 180, 220, 245, 256, 262, 266, 271, 274, 277],
      vObsErr: [6, 5, 5, 4, 4, 4, 4, 5, 5, 5],
      vAcm: [138, 179, 219, 244, 257, 264, 269, 272, 275, 278],
      vMond: [132, 171, 210, 231, 240, 244, 247, 249, 250, 251],
      vGas: [10, 13, 16, 18, 20, 22, 23, 24, 24, 24],
      vDisk: [120, 154, 182, 201, 211, 216, 218, 219, 219, 219],
      vBulge: [38, 46, 52, 53, 50, 46, 42, 36, 30, 24]
    }
  }
];
