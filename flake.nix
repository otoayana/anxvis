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
          };
        in with pkgs; {
          packages.default = with python312Packages; buildPythonApplication {
              pname = "anxvis";
              version = "0.1.0";
              pyproject = true;
              nativeBuildInputs = [
                poetry-core
              ];
              dependencies = [
                imageio
                imageio-ffmpeg
                numpy
                pillow
                pygame
                requests
                soundfile
                tqdm
              ];
              src = ./.;
            };
          devShells.default = mkShell {
            buildInputs = with python312Packages; [
              imageio
              imageio-ffmpeg
              numpy
              pillow
              pygame
              requests
              soundfile
              tqdm
              python-lsp-server
            ];
          };
        }
      );
}
