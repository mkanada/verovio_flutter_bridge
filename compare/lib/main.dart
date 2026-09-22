/// Ponto de entrada da ferramenta `compare` (Flutter/Linux).
///
/// Comandos: `diff` (comparação pixel a pixel entre PNGs) e `scene-to-png`
/// (R02d: renderiza uma página de um `.vsb` num PNG). O renderizador SVG de
/// referência continua no binário Rust `compare/svg_render/`.
library;

import 'dart:io';

import 'package:args/args.dart';
import 'package:flutter/widgets.dart';

import 'src/diff.dart';
import 'src/scene_to_png.dart';

ArgParser _commands() {
  final parser = ArgParser();
  parser.addFlag(
    'help',
    abbr: 'h',
    defaultsTo: false,
    negatable: false,
    help: 'Exibe esta ajuda.',
  );
  final diffParser = ArgParser()
    ..addOption('tolerance', defaultsTo: '0')
    ..addFlag(
      'help',
      abbr: 'h',
      defaultsTo: false,
      negatable: false,
      help: 'Exibe ajuda do diff.',
    );
  parser.addCommand('diff', diffParser);
  final sceneToPngParser = ArgParser()
    ..addOption('page', defaultsTo: '1', help: 'Número da página (1-based).')
    ..addOption(
      'alternate',
      help:
          'xml:id do compasso de chegada (§2.5): desenha a página --page '
          'dessa sequência alternativa, não a normal.',
    )
    ..addOption('width', help: 'Largura do PNG (padrão: widthPx da página).')
    ..addOption('height', help: 'Altura do PNG (padrão: heightPx da página).')
    ..addFlag(
      'help',
      abbr: 'h',
      defaultsTo: false,
      negatable: false,
      help: 'Exibe ajuda do scene-to-png.',
    );
  parser.addCommand('scene-to-png', sceneToPngParser);
  return parser;
}

void _usage(ArgParser parser) {
  stderr.writeln('Uso: compare <comando> [opções]');
  stderr.writeln('');
  stderr.writeln('Comandos: diff, scene-to-png.');
  stderr.writeln(parser.usage);
}

int _parseIntOption(String name, String? raw) {
  if (raw == null || raw.isEmpty) {
    throw FormatException('opção --$name exige um valor inteiro');
  }
  final value = int.tryParse(raw);
  if (value == null) {
    throw FormatException('opção --$name: "$raw" não é um inteiro');
  }
  return value;
}

Future<void> _runDiff(ArgResults command) async {
  if (command['help'] as bool) {
    stdout.writeln(
      'Uso: compare diff <a.png> <b.png> <saida.png> '
      '[--tolerance N] [--help]',
    );
    return;
  }
  if (command.rest.length != 3) {
    stderr.writeln('Erro: diff <a.png> <b.png> <saida.png>');
    exit(2);
  }
  try {
    final result = diffPngFiles(
      command.rest[0],
      command.rest[1],
      command.rest[2],
      tolerance: int.parse(command['tolerance'] as String),
    );
    stdout.writeln(result);
  } on FormatException catch (e) {
    stderr.writeln('Erro: ${e.message}');
    exit(2);
  } catch (e) {
    stderr.writeln('Erro: $e');
    exit(1);
  }
}

Future<void> _runSceneToPng(ArgResults command) async {
  if (command['help'] as bool) {
    stdout.writeln(
      'Uso: compare scene-to-png <entrada.vsb|json> <saida.png> '
      '[--page N] [--alternate <start-id>] [--width W] [--height H] '
      '[--help]',
    );
    return;
  }
  if (command.rest.length != 2) {
    stderr.writeln('Erro: scene-to-png <entrada.vsb|json> <saida.png>');
    exit(2);
  }
  try {
    final page = _parseIntOption('page', command['page'] as String?);
    final alternateStart = command['alternate'] as String?;
    final widthRaw = command['width'] as String?;
    final heightRaw = command['height'] as String?;
    await sceneToPng(
      command.rest[0],
      command.rest[1],
      page1Based: page,
      alternateStart: alternateStart,
      width: widthRaw == null ? null : _parseIntOption('width', widthRaw),
      height: heightRaw == null ? null : _parseIntOption('height', heightRaw),
    );
    final where = alternateStart == null
        ? 'página $page'
        : 'página $page da sequência "$alternateStart"';
    stdout.writeln('Gravado ${command.rest[1]} ($where).');
  } on FormatException catch (e) {
    stderr.writeln('Erro: ${e.message}');
    exit(2);
  } catch (e) {
    stderr.writeln('Erro: $e');
    exit(1);
  }
}

Future<void> main(List<String> args) async {
  WidgetsFlutterBinding.ensureInitialized();
  final parser = _commands();
  ArgResults results;
  try {
    results = parser.parse(args);
  } on FormatException catch (e) {
    stderr.writeln('Erro: ${e.message}');
    _usage(parser);
    exit(2);
  }

  if (results['help'] as bool) {
    stdout.writeln('Uso: compare <comando> [opções]');
    stdout.writeln('');
    stdout.writeln('Comandos: diff, scene-to-png.');
    stdout.writeln(parser.usage);
    exit(0);
  }

  final command = results.command;
  if (command == null) {
    _usage(parser);
    exit(2);
  }
  switch (command.name) {
    case 'diff':
      await _runDiff(command);
    case 'scene-to-png':
      await _runSceneToPng(command);
    default:
      _usage(parser);
      exit(2);
  }
  exit(0);
}
