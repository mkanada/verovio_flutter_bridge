# verovio (Dart FFI bindings)

Dart bindings for the Verovio `Toolkit` — including this fork's native
`.vsb` (Verovio Score Bridge) exporter — built the same way as
[`csa8820/verovio_flutter`](https://github.com/csa8820/verovio_flutter):
a plain C API (`extern "C"`) wraps the C++ `Toolkit` class, compiled into a
shared library, loaded from Dart with `dart:ffi`. See
`../../../docs/plano/P02a-libverovio-e-wrapper.md` for the D-RUNTIME
decision this exists to serve and for the measured build numbers.

## Layout

```
lib/
  verovio.dart              public export (VerovioToolkit, VerovioBindings)
  src/verovio_bindings.dart low-level dart:ffi signatures, 1:1 with ../../tools/c_wrapper.h
  src/verovio_toolkit.dart  idiomatic VerovioToolkit class (one method per C function)
build_linux_so.sh           builds libverovio.so and copies it here
example/main.dart           CLI-style usage example
test/verovio_toolkit_test.dart  end-to-end test against a real corpus file
```

## Build the native library (Linux)

```sh
./build_linux_so.sh
```

This runs `cmake -DBUILD_AS_LIBRARY=ON` against `../../cmake` (the same
CMake project used by every other binding here), builds into
`../../tools/build-library/`, and copies `libverovio.so` next to this
README so `DynamicLibrary.open('libverovio.so')` finds it when the working
directory is `bindings/dart/`. Re-run it whenever `verovio/src` or
`tools/c_wrapper.*` changes.

## Use it

```sh
dart pub get
dart run example/main.dart ../../../corpus/mei/Grieg_Little_bird_Op43_No4.mei out.vsb
```

```dart
import 'package:verovio/verovio.dart';

final toolkit = VerovioToolkit.withResourcePath('../../data'); // Bravura/Leipzig fonts
toolkit.loadFile('score.mei');
toolkit.renderToBridgeFile('score.vsb');  // whole score as a package, -t vsb
final json = toolkit.renderToBridgeJson(); // every page as one JSON, -t vsb-json
toolkit.dispose();
```

`VerovioToolkit` exposes the full `c_wrapper.h` surface (loading, SVG,
MIDI, PAE, Humdrum conversion, timemap, expansion map, editor actions,
options, and the two bridge renderers), not just the methods shown
above.

## Run the tests

```sh
./build_linux_so.sh   # if you haven't already
dart test
```

The suite loads a real corpus MEI file and exercises the FFI path against
the freshly built `.so`: page count, SVG rendering, the `.vsb` package
(zip `PK` magic plus the three mandatory entry names) and `vsb-json` (valid
JSON whose page count matches `getPageCount()`). `score_bridge`, the real
parser, needs `dart:ui` and cannot be imported from a plain `dart test`;
the end-to-end parse check is recorded in P02a's execution notes.

## Platform coverage

| Platform | Status |
| --- | --- |
| Linux (x86_64) | Built and tested here (`build_linux_so.sh`, `dart test` — see E01 execution notes) |
| macOS / Windows desktop | Same CMake target (`-DBUILD_AS_LIBRARY=ON`) builds `libverovio.dylib`/`verovio.dll` there; `VerovioToolkit._openLibrary` already picks the right default name. Not built/tested in this environment (no macOS/Windows toolchain here). |
| Android | Built here with `build_android_so.sh` (`-DBUILD_AS_ANDROID_LIBRARY=ON` + NDK toolchain, one `.so` per ABI under `android-libs/<abi>/`). See P02a's execution notes for the NDK version and the per-ABI sizes. No Gradle/JNI host project was written — that is P02b. |
| iOS | Same `c_wrapper.h` an XCFramework would wrap; `_openLibrary` already falls back to `DynamicLibrary.process()` for a statically linked host. Not exercised here (no Xcode/iOS SDK in this environment). |
| Web (WASM) | Out of scope: the `.vsb` path targets a Flutter app with a native library, not the browser. `../../emscripten/` still holds the upstream toolchain if it is ever needed. |

## Notes

- String returns from the toolkit (`vrvToolkit_get*`/`render*`) point into
  a buffer owned by the C++ `Toolkit` instance (`SetCString`/`GetCString`)
  — `VerovioToolkit` copies them into a Dart `String` and never frees that
  pointer, same as the Swift binding.
- `.vsb` output is a binary zip; it can only be written to a file
  (`renderToBridgeFile`), the same restriction the CLI has (`-o -` to
  stdout is not supported for that format). `renderToBridgeJson` is text
  and does come back as a `String`.
- One `VerovioToolkit` wraps one native `Toolkit` instance. It is not
  thread-safe — same rule as the C++ class itself.
