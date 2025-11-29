{ pkgs }: {
  deps = [
    pkgs.stunnel
    pkgs.tmux
    pkgs.ffmpeg
    pkgs.pkg
    pkgs.bashInteractive
    pkgs.nodePackages.bash-language-server
    pkgs.man
  ];
}