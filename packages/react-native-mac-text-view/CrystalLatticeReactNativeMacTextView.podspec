require "json"

package = JSON.parse(File.read(File.join(__dir__, "package.json")))

Pod::Spec.new do |s|
  s.name         = "CrystalLatticeReactNativeMacTextView"
  s.version      = package["version"]
  s.summary      = package["description"]
  s.homepage     = "https://github.com/crystal-lattice/react-native-mac-text-view"
  s.license      = "MIT"
  s.author       = "Crystal Lattice"
  s.source       = { :git => "https://github.com/crystal-lattice/react-native-mac-text-view.git", :tag => s.version.to_s }
  s.source_files = "apple/**/*.{h,m,mm}"
  s.requires_arc = true
  s.platforms    = { :osx => "12.4" }

  if defined?(install_modules_dependencies()) != nil
    install_modules_dependencies(s)
  else
    s.dependency "React-Core"
  end
end