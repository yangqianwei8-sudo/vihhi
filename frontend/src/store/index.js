import { createStore } from 'vuex'

export default createStore({
  state: {
    user: null,
    token: null
  },
  mutations: {
    SET_USER(state, user) {
      state.user = user
    },
    SET_TOKEN(state, token) {
      state.token = token
    }
  },
  actions: {
    setUser({ commit }, user) {
      commit('SET_USER', user)
    },
    setToken({ commit }, token) {
      commit('SET_TOKEN', token)
    }
  },
  modules: {
  }
})

