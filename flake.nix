{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };
  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem
      (system:
        let 
          pkgs = import nixpkgs {
            inherit system;
            overlays = [(self: super: {
              python312 = super.python312.override {
                packageOverrides = pySelf: pySuper: {
                  pillow-simd = pySuper.pillow-simd.overrideAttrs (attrs: {
                    doCheck = false;
                    doInstallCheck = false;
                  });
                };
              };
            })];
          };
        in with pkgs; {
          packages.default = with python312Packages; buildPythonApplication {
              pname = "anxvis";
              version = "0.1.0";
              pyproject = true;
              nativeBuildInputs = [
                poetry-core
              ];
              buildInputs = [
                ffmpeg
              ];
              dependencies = [
                imageio
                imageio-ffmpeg
                numpy
                pillow-simd
                pygame
                requests
                soundfile
                tqdm
              ];
              src = ./.;
            };
          devShells.default = mkShell {
            buildInputs = with pkgs; [
              ffmpeg
              poetry

              (with python312Packages; [
                # Dependencies
                imageio
                imageio-ffmpeg
                numpy
                pillow-simd
                pygame
                requests
                soundfile
                tqdm

                # Utilities
                pre-commit
                python-lsp-server
                ruff
              ])
            ];
          };
        }
      );
}
