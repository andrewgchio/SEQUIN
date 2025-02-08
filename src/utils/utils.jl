# General utility functions

# Implementation of an iterator that produces n items at a time
struct TakeNItems{T}
    iterable::T
    n::Int
end
Base.eltype(::Type{TakeNItems{T}}) where {T} = Vector{eltype(T)}
Base.IteratorSize(::Type{<:TakeNItems}) = Base.HasLength()
Base.length(it::TakeNItems) = ceil(Int, length(it.iterable) / it.n)

Base.iterate(it::TakeNItems) = iterate(it, 1)

function Base.iterate(it::TakeNItems, state)
    (it.n <= 0) && throw(ArgumentError("n must be a positive integer."))

    (state > length(it.iterable)) && return nothing

    return (
        [it.iterable[i] for i in state:min(state + it.n - 1, length(it.iterable))],
        state + it.n
    )
end

take_n_items(iterable, n::Int=1) = TakeNItems(iterable, n)
