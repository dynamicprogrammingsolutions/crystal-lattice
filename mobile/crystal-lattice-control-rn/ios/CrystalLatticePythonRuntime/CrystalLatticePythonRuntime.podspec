Pod::Spec.new do |spec|
  spec.name = 'CrystalLatticePythonRuntime'
  spec.version = '0.1.0'
  spec.summary = 'Embedded CPython host for Crystal Lattice Control.'
  spec.homepage = 'https://github.com/dynamicprogrammingsolutions/crystal-lattice'
  spec.license = { :type => 'Apache-2.0' }
  spec.author = { 'Dynamic Programming Solutions Kft.' => 'ferenci84@gmail.com' }
  spec.source = { :git => 'https://github.com/dynamicprogrammingsolutions/crystal-lattice.git' }
  spec.platform = :ios, '15.1'
  spec.swift_version = '5.0'
  spec.static_framework = true

  spec.source_files = 'Sources/**/*.{h,m,swift}'
  spec.public_header_files = 'Sources/CLPythonHostSupport.h'
  spec.vendored_frameworks = 'Vendor/Python.xcframework'
  spec.resource_bundles = {
    'CrystalLatticePythonRuntimeResources' => ['Resources/python312.zip']
  }

  spec.dependency 'React-Core'
end