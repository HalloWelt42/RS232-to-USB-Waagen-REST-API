import { describe, it, expect } from 'vitest';
import { buildHelpVars, renderHelpBody } from '../src/lib/helpRender';
import type { ScaleModel } from '../src/lib/types';

const PLC: ScaleModel = {
  id: 'gg.plc.6000', manufacturer: 'G&G', series: 'PLC', name: 'PLC-6000 (6000 g / 0,1 g)',
  category: 'precision', max_g: 6000, resolution_g: 0.1,
  default_baudrate: 9600, rs232: true, note: '',
  min_load_g: 5, linearity_g: 0.2, repeatability_g: 0.1,
  stabilization_s: 3, warmup_min: 30, operating_temp_c: [10, 30],
};

const ANALYTICAL: ScaleModel = {
  id: 'gg.jjbc.224', manufacturer: 'G&G', series: 'JJ-BC', name: 'JJ-BC 224 (220 g / 0,1 mg)',
  category: 'analytical', max_g: 220, resolution_g: 0.0001,
  default_baudrate: 9600, rs232: true, note: '',
  min_load_g: 0.01, linearity_g: 0.0002, repeatability_g: 0.0001,
  stabilization_s: 5, warmup_min: 60, operating_temp_c: [15, 25],
};

describe('buildHelpVars', () => {
  it('formats model name as Manufacturer Series-Short', () => {
    const v = buildHelpVars(PLC);
    expect(v.modelName).toBe('G&G PLC-PLC-6000');
  });

  it('immer in Grundeinheit Gramm — keine kg-Umrechnung', () => {
    expect(buildHelpVars(PLC).maxG).toBe('6000 g');
    expect(buildHelpVars(ANALYTICAL).maxG).toBe('220 g');
  });

  it('uses comma as decimal separator (DE-Hilfe-Default)', () => {
    expect(buildHelpVars(PLC).resolutionG).toBe('0,1 g');
    expect(buildHelpVars(ANALYTICAL).resolutionG).toBe('0,0001 g');
  });

  it('recommends a higher minimum-pieces count for finer resolutions', () => {
    expect(buildHelpVars(PLC).minPiecesUnder1g).toBe(20);
    // bei 0,0001 g würde Math.round(2/0.0001)=20000 sein → wird auf 50 begrenzt
    expect(buildHelpVars(ANALYTICAL).minPiecesUnder1g).toBe(50);
  });
});

describe('renderHelpBody', () => {
  const vars = buildHelpVars(PLC);

  it('replaces placeholders', () => {
    expect(renderHelpBody('Auflösung {{resolutionG}}', vars)).toContain('0,1 g');
    expect(renderHelpBody('Maximal {{maxG}}', vars)).toContain('6000 g');
  });

  it('keeps unknown placeholders intact', () => {
    expect(renderHelpBody('{{unknown}}', vars)).toBe('{{unknown}}');
  });

  it('converts tool cross-links into buttons with data-route-tool', () => {
    const html = renderHelpBody('siehe [[tool:count|Stückzählung]]', vars);
    expect(html).toContain('data-route-tool="count"');
    expect(html).toContain('>Stückzählung<');
  });

  it('converts help cross-links into buttons with data-route-help', () => {
    const html = renderHelpBody('siehe [[help:wiegen|Wiegen]]', vars);
    expect(html).toContain('data-route-help="wiegen"');
  });

  it('preserves <strong> markup around placeholders', () => {
    const html = renderHelpBody('Auflösung <strong>{{resolutionG}}</strong>', vars);
    expect(html).toContain('<strong>0,1 g</strong>');
  });
});
