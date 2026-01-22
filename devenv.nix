{ pkgs, lib, config, inputs, ... }:

{
  # https://devenv.sh/basics/
  env = {
    GREET = "taskdantic";
    #TASKRC_PATH = "${$DEVENV_ROOT}/examples";
    };
  
  dotenv.enable = true;

  # https://devenv.sh/packages/
  packages = with pkgs; [ 
    git 
    uv
    ];

  # https://devenv.sh/languages/
  # languages.rust.enable = true;
  languages = {
      python = {
          enable = true;
          version = "3.13";
          venv.enable = true;
          uv.enable = true;
        };
    };

  # https://devenv.sh/processes/
  # processes.cargo-watch.exec = "cargo-watch";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/scripts/
  scripts.hello.exec = ''
    echo hello from $GREET @ $DEVENV_ROOT
  '';

  scripts.setenv.exec = ''
    export TASKRC_PATH=$DEVENV_ROOT/examples/.taskrc
    echo $TASKRC_PATH
    export TASKDANTIC_TASKS_ROOT=$DEVENV_ROOT/examples/uda
    echo $TASKDANTIC_TASKS_ROOT
    '';

  enterShell = ''
    hello
    echo
    setenv
    echo
    git --version
    echo
  '';

  # https://devenv.sh/tasks/
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };

  # https://devenv.sh/tests/
  enterTest = ''
    echo "Running tests"
    git --version | grep --color=auto "${pkgs.git.version}"
  '';

  # https://devenv.sh/pre-commit-hooks/
  # pre-commit.hooks.shellcheck.enable = true;

  # See full reference at https://devenv.sh/reference/options/
}
