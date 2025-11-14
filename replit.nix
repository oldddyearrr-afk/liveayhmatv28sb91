{ pkgs }: {
  deps = [
    pkgs.pkg
    pkgs.bashInteractive
    pkgs.nodePackages.bash-language-server
    pkgs.man
  ];
}