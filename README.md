# README

## Overview
This package provides **templates for experiments** built on top of [quflow](https://github.com/...), a graph-based execution framework. Each template enforces a consistent structure for running an experiment, with a required `execute()` method (to run the logic) and an upcoming `export()` method (for saving data/results). By leveraging Qucraft's core concepts (Tasks, Nodes, Channels, Workflow), these templates allow you to define your experiment steps in a straightforward and extensible way.

## Getting Started
1. **Installation**: Install Qucraft and this package (e.g., via `pip install .` in your local environment).
2. **Create a Template Subclass**: Inherit from one of the provided base classes to implement your custom experiment flow—each subclass must implement its own `execute()` method.
3. **Run**: Instantiating and calling `.execute()` on your subclass orchestrates all tasks (e.g., data fetching, processing, plotting) in the correct order.

## Example
Below is a **simple demonstration** of creating and using a custom experiment template. For more complex examples, see the dedicated example files in this repository.

```python

