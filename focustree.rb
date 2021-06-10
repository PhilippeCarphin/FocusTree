# Documentation: https://docs.brew.sh/Formula-Cookbook
#                https://rubydoc.brew.sh/Formula
# PLEASE REMOVE ALL GENERATED COMMENTS BEFORE SUBMITTING YOUR PULL REQUEST!
class Focustree < Formula
  desc "FocusTree"
  homepage "https://github.com/philippecarphin/focustree"
  url "https://github.com/philippecarphin/focustree.git"
  version "1.0.0"
  sha256 ""
  license ""

  depends_on "cmake" => :build
  depends_on "pandoc" => :build
  # depends_on "python3" => :build

  def install
    # ENV.deparallelize  # if your formula fails when building in parallel
    # Remove unrecognized options if warned by configure
    # https://rubydoc.brew.sh/Formula.html#std_configure_args-instance_method
    system "cmake", "-S", ".", "-B", "build", *std_cmake_args
    system "cmake", "--build", "build", "--target", "install"
    # system "python3", "-m", "pip", "install", "-r", "requirements.txt"
  end

  def caveats
    s = <<~EOS
      I am still figuring out how to package the python dependencies of this project with the homebrew formula.

      In the meantime, please run

        python3 -m pip termcolor prompt-toolkit Pygments requests termcolor

      Thank you
    EOS
    s
  end

  test do
    # `test do` will create, run in and delete a temporary directory.
    #
    # This test will fail and we won't accept that! For Homebrew/homebrew-core
    # this will need to be a test that verifies the functionality of the
    # software. Run the test with `brew test focustree`. Options passed
    # to `brew install` such as `--HEAD` also need to be provided to `brew test`.
    #
    # The installed folder is not in the path, so use the entire path to any
    # executables being tested: `system "#{bin}/program", "do", "something"`.
    system "false"
  end
end
