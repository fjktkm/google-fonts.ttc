# google-fonts.ttc

This repository builds a single TrueType Collection containing all Google Fonts.

## Usage

### Dataset

When the repository is opened in its Dev Container, the Google Fonts dataset is
downloaded automatically. Without the Dev Container, initialize the submodule
manually:

```console
git submodule update --init --depth 1 data/google/fonts
```

### Build

Run the builder with uv:

```console
uv run main.py
```

The collection is written to `output/google-fonts.ttc`.

## Windows compatibility

### Font metadata

This is a technical experiment, so the result should also open on Windows.
[`Gidugu-Regular.ttf`](https://github.com/google/fonts/issues/9982) cannot be
installed on Windows because its `name` table lacks the Windows Name ID 3 record.
The build adds that record in memory from the font's version, vendor ID, and
PostScript name before writing the collection; the source font is not changed.

### Collection size

A boundary test with Windows GDI's
[`AddFontResourceExW`](https://learn.microsoft.com/windows/win32/api/wingdi/nf-wingdi-addfontresourceexw)
accepted the collection at 2,147,483,647 bytes and rejected the same collection at
2,147,483,648 bytes (2 GiB). This is a Windows implementation limit, not the
[OpenType format limit](https://learn.microsoft.com/typography/opentype/spec/otff),
whose collection offsets are unsigned 32-bit values.

To remain below the Windows limit, every font is processed with HarfBuzz Subset
while retaining all Unicode code points and glyphs. The process removes TrueType
hinting, optimizes variable-font IUP deltas, and otherwise follows HarfBuzz's
default subsetting policy.

## Distribution

The current checkout contains 3,793 font files from 2,048 families, counting only
files directly inside each family directory and excluding alternate builds in
subdirectories: 3,715 files are under the SIL Open Font License, 61 under the
Apache License 2.0, and 17 under the Ubuntu Font Licence. The generated TTC is not
ready for redistribution:

| License | Current issue |
| --- | --- |
| [SIL Open Font License](https://openfontlicense.org/ofl-faq/) | HarfBuzz removes hinting and rewrites font data, so claiming functional equivalence is not straightforward. At least 555 included families declare Reserved Font Names, which modified versions may not use without satisfying the OFL requirements. |
| [Ubuntu Font Licence](https://canonical.com/legal/font-licence) | The five included Ubuntu families become Modified Versions when converted and optimized. The UFL requires a distinguishing derivative name, which this build does not add. |
| [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) | Redistribution requires the license and retained notices, and modified files must carry prominent change notices. This build does not create that accompanying material. |

HarfBuzz's default subsetting policy can also remove nonessential `name` records,
including some author, vendor, and project URL fields. Although copyright records
are retained, the per-family license files and notices are not embedded in the TTC.
The repository therefore distributes only the build code, not
`output/google-fonts.ttc`.

## License

The original code in this repository is licensed under the
[MIT License](LICENSE). This license and its copyright notice apply only to the
repository's code and documentation. They do not apply to the Google Fonts
submodule or to the generated font collection; each included font remains subject
to its own copyright and license terms.
