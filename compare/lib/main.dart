/// Ponto de entrada da ferramenta `compare` (Flutter/Linux).
///
/// Nesta etapa o binário expõe somente o comando `diff`; o renderizador SVG
/// continua no binário Rust `compare/svg_render/`.
library;

import 'dart:io';

import 'package:args/args.dart';
import 'package:flutter/widgets.dart';

import 'src/diff.dart';

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
  return parser;
}

void _usage(ArgParser parser) {
  stderr.writeln('Uso: compare diff <a.png> <b.png> <saida.png> [opções]');
  stderr.writeln('');
  stderr.writeln('Comandos: diff.');
  stderr.writeln(parser.usage);
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
    stdout.writeln('Comandos: diff.');
    stdout.writeln(parser.usage);
    exit(0);
  }

  final command = results.command;
  if (command == null || command.name != 'diff') {
    _usage(parser);
    exit(2);
  }
  if (command['help'] as bool) {
    stdout.writeln(
      'Uso: compare diff <a.png> <b.png> <saida.png> '
      '[--tolerance N] [--help]',
    );
    exit(0);
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
  exit(0);
}
