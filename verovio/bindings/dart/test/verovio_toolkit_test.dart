@TestOn('linux')
library;

import 'dart:convert';
import 'dart:io';

import 'package:test/test.dart';
import 'package:verovio/verovio.dart';

// corpus/mei/Grieg_Little_bird_Op43_No4.mei is one of the ten corpus pieces
// the CLI exporter is measured against (see corpus/README.md), so a working
// export from it is a meaningful smoke test rather than a synthetic fixture.
//
// score_bridge (the real .vsb parser) needs dart:ui and therefore cannot be
// imported from a plain `dart test`; these tests check the package shape
// without it. The end-to-end parser check lives in P02a's execution notes.
String _repoRoot() {
  var dir = Directory.current;
  while (!File('${dir.path}/CLAUDE.md').existsSync()) {
    final parent = dir.parent;
    if (parent.path == dir.path) {
      throw StateError('Could not locate repo root from ${Directory.current}');
    }
    dir = parent;
  }
  return dir.path;
}

void main() {
  final repoRoot = _repoRoot();
  final resourcePath = '$repoRoot/verovio/data';
  final sampleMei = '$repoRoot/corpus/mei/Grieg_Little_bird_Op43_No4.mei';

  test('loads a MEI file and reports pages', () {
    final toolkit = VerovioToolkit.withResourcePath(resourcePath);
    addTearDown(toolkit.dispose);

    expect(toolkit.getVersion(), isNotEmpty);
    expect(toolkit.loadFile(sampleMei), isTrue);
    expect(toolkit.getPageCount(), greaterThan(0));
  });

  test('renders SVG for page 1', () {
    final toolkit = VerovioToolkit.withResourcePath(resourcePath);
    addTearDown(toolkit.dispose);

    expect(toolkit.loadFile(sampleMei), isTrue);
    final svg = toolkit.renderToSVG(1);
    expect(svg, contains('<svg'));
  });

  test('renders a whole-score .vsb package', () {
    final toolkit = VerovioToolkit.withResourcePath(resourcePath);
    addTearDown(toolkit.dispose);

    expect(toolkit.loadFile(sampleMei), isTrue);

    final outFile =
        File('${Directory.systemTemp.path}/verovio_dart_ffi_test.vsb');
    addTearDown(() {
      if (outFile.existsSync()) outFile.deleteSync();
    });

    expect(toolkit.renderToBridgeFile(outFile.path), isTrue);
    expect(outFile.existsSync(), isTrue);

    final bytes = outFile.readAsBytesSync();
    // .vsb packages are zip archives: "PK\x03\x04" local-file-header magic is
    // the cheapest correctness check without a zip dependency.
    expect(bytes.length, greaterThan(1000));
    expect(bytes.sublist(0, 4), equals([0x50, 0x4b, 0x03, 0x04]));
    // Entry names sit uncompressed in the local file headers, so the three
    // mandatory documents of the spec are visible in the raw bytes.
    final raw = latin1.decode(bytes);
    for (final entry in ['manifest.json', 'scene.json', 'glyphs.json']) {
      expect(raw, contains(entry), reason: 'missing zip entry $entry');
    }
  });

  test('renders every page as one vsb-json document', () {
    final toolkit = VerovioToolkit.withResourcePath(resourcePath);
    addTearDown(toolkit.dispose);

    expect(toolkit.loadFile(sampleMei), isTrue);

    final decoded = jsonDecode(toolkit.renderToBridgeJson());
    expect(decoded, isA<Map<String, dynamic>>());
    final doc = decoded as Map<String, dynamic>;
    expect(doc['glyphs'], isNotEmpty);

    final pages = (doc['scene'] as Map<String, dynamic>)['pages'] as List;
    // The whole document, not just page 1 - same default as the CLI's -a.
    expect(pages, hasLength(toolkit.getPageCount()));
  });
}
