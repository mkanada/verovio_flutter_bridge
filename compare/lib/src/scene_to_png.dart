/// Comando `scene-to-png` (R02d): renderiza uma página de um `.vsb` (ou de um
/// JSON único `-t vsb-json`) num PNG, com o mesmo fundo branco opaco e as
/// mesmas dimensões do PNG de referência do `svg_render`.
///
/// É o render mínimo de conferência visual: formas `p`/`r`/`e`, glifos `u`
/// (R03) e runs de texto `t` (R04b/R04c, três alinhamentos). O critério aqui
/// é alinhamento, não percentual.
library;

import 'dart:io';
import 'dart:ui' as ui;

import 'package:score_bridge/score_bridge.dart';

/// Renderiza a página [page1Based] (número de página 1-based, como o `-p` do
/// Verovio) de [inputPath] em [outputPath].
///
/// [alternateStart] (P02d, §2.5): quando dado, a página vem de
/// `doc.alternateStartingAt(alternateStart)` em vez de `doc.pages` — a
/// sequência alternativa cujo compasso de chegada é esse `xml:id`, não o
/// documento inteiro. `page1Based` continua 1-based, agora **dentro da
/// sequência**.
///
/// [width]/[height] omitidos viram `page.widthPx`/`page.heightPx` (que são as
/// dimensões do `<svg>` raiz e, portanto, do PNG do `svg_render`).
Future<void> sceneToPng(
  String inputPath,
  String outputPath, {
  required int page1Based,
  String? alternateStart,
  int? width,
  int? height,
}) async {
  final bytes = await File(inputPath).readAsBytes();
  final doc = VsbDocument.fromBytes(bytes);

  final List<ScenePage> pages;
  if (alternateStart != null) {
    final sequence = doc.alternateStartingAt(alternateStart);
    if (sequence == null) {
      throw ArgumentError(
        'nenhuma sequência alternativa começa em "$alternateStart" '
        '(sequências: ${doc.alternates.map((s) => s.start).join(", ")})',
      );
    }
    pages = sequence.pages;
  } else {
    pages = doc.pages;
  }

  if (page1Based < 1 || page1Based > pages.length) {
    final scope = alternateStart == null
        ? 'o documento'
        : 'a sequência "$alternateStart"';
    throw ArgumentError(
      'página $page1Based fora do intervalo ($scope tem '
      '${pages.length} página(s); --page é 1-based, como o -p do Verovio)',
    );
  }
  final page = pages[page1Based - 1];
  final w = width ?? page.widthPx;
  final h = height ?? page.heightPx;
  if (w <= 0 || h <= 0) {
    throw ArgumentError('dimensões inválidas: ${w}x$h');
  }

  // Texto comum (R04b) precisa das TTFs do pacote registradas no motor;
  // sem isto o Flutter cai em fallback silencioso (R04a).
  await loadScoreFonts();
  final recorder = ui.PictureRecorder();
  final canvas = ui.Canvas(recorder);
  // Fundo branco opaco, como o `svg_render` compõe (senão o diff acusa a
  // página inteira). Vai antes da transformação de página do pintor, em
  // pixels de saída.
  canvas.drawRect(
    ui.Rect.fromLTWH(0, 0, w.toDouble(), h.toDouble()),
    ui.Paint()..color = const ui.Color(0xFFFFFFFF),
  );
  ScenePainter(page, doc.glyphs).paint(canvas);
  final picture = recorder.endRecording();
  try {
    final image = await picture.toImage(w, h);
    try {
      final png = await image.toByteData(format: ui.ImageByteFormat.png);
      if (png == null) {
        throw StateError('falha ao codificar o PNG de $outputPath');
      }
      await File(outputPath).writeAsBytes(png.buffer.asUint8List());
    } finally {
      image.dispose();
    }
  } finally {
    picture.dispose();
  }
}
