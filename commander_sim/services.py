"""Explicit, per-game service composition; no deck or card dependencies."""
from dataclasses import dataclass
from types import MappingProxyType

class ServiceConfigurationError(ValueError):
    """Invalid service graph; raised before any service factory runs."""

@dataclass(frozen=True)
class ServiceDefinition:
    name:str
    factory:object
    dependencies:tuple[str,...]

class ServiceRegistry:
    def __init__(self):self._definitions={}
    def register(self,name,factory,*,dependencies=()):
        if not isinstance(name,str) or not name or name in self._definitions:raise ServiceConfigurationError('Invalid or duplicate service: '+str(name))
        if not callable(factory):raise ServiceConfigurationError('Service factory must be callable')
        deps=tuple(dependencies)
        if any(not isinstance(d,str) or not d for d in deps) or len(set(deps))!=len(deps):raise ServiceConfigurationError('Invalid service dependencies')
        self._definitions[name]=ServiceDefinition(name,factory,deps)
    def build(self):
        # Validate the entire graph before calling any factory.
        ordered=[];state={}
        def visit(name):
            if name not in self._definitions:raise ServiceConfigurationError('Missing service: '+name)
            if state.get(name)==1:raise ServiceConfigurationError('Cyclic service dependency: '+name)
            if state.get(name)==2:return
            state[name]=1
            for dep in self._definitions[name].dependencies:visit(dep)
            state[name]=2;ordered.append(name)
        for name in self._definitions:visit(name)
        services={}
        for name in ordered:
            spec=self._definitions[name]
            services[name]=spec.factory(MappingProxyType({d:services[d] for d in spec.dependencies}))
        return MappingProxyType(services)
